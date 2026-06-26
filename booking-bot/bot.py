"""
Booking bot — клиент выбирает услугу, дату, время и оставляет заявку.
Продаётся малому бизнесу (барберы, мастера, врачи, репетиторы).
Цена: $150-300 разработка + $30/мес поддержка.
"""
import asyncio
import os
import sqlite3
import logging
from datetime import datetime, date, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Наш сервис")
SERVICES = [s.strip() for s in os.getenv("SERVICES", "Консультация,Услуга 1,Услуга 2").split(",")]
WORK_HOURS = list(range(int(os.getenv("WORK_START", "9")), int(os.getenv("WORK_END", "19"))))

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# --- Database ---
def init_db():
    conn = sqlite3.connect("bookings.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            username    TEXT,
            first_name  TEXT,
            phone       TEXT,
            service     TEXT,
            date        TEXT,
            time        TEXT,
            status      TEXT DEFAULT 'pending',
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def save_booking(user_id, username, first_name, phone, service, book_date, book_time):
    conn = sqlite3.connect("bookings.db")
    conn.execute(
        "INSERT INTO bookings (user_id, username, first_name, phone, service, date, time) VALUES (?,?,?,?,?,?,?)",
        (user_id, username, first_name, phone, service, book_date, book_time)
    )
    conn.commit()
    conn.close()


def get_booked_times(book_date: str) -> list[str]:
    conn = sqlite3.connect("bookings.db")
    rows = conn.execute(
        "SELECT time FROM bookings WHERE date = ? AND status != 'cancelled'", (book_date,)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_all_bookings(status=None) -> list:
    conn = sqlite3.connect("bookings.db")
    if status:
        rows = conn.execute("SELECT * FROM bookings WHERE status = ? ORDER BY date, time", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bookings ORDER BY date DESC, time DESC LIMIT 50").fetchall()
    conn.close()
    return rows


def update_status(booking_id: int, status: str):
    conn = sqlite3.connect("bookings.db")
    conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
    conn.commit()
    conn.close()


init_db()


# --- FSM States ---
class BookingState(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_phone = State()
    confirming = State()


# --- Keyboards ---
def services_kb() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=s, callback_data=f"svc:{s}")] for s in SERVICES]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def dates_kb() -> InlineKeyboardMarkup:
    buttons = []
    today = date.today()
    for i in range(1, 8):
        d = today + timedelta(days=i)
        label = d.strftime("%d.%m (%a)").replace("Mon","Пн").replace("Tue","Вт").replace("Wed","Ср").replace("Thu","Чт").replace("Fri","Пт").replace("Sat","Сб").replace("Sun","Вс")
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"date:{d.isoformat()}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def times_kb(booked: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for h in WORK_HOURS:
        t = f"{h:02d}:00"
        if t in booked:
            row.append(InlineKeyboardButton(text=f"❌{t}", callback_data="booked"))
        else:
            row.append(InlineKeyboardButton(text=t, callback_data=f"time:{t}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")],
    ])


# --- Handlers ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👋 Добро пожаловать в {BUSINESS_NAME}!\n\n"
        f"Нажмите кнопку ниже чтобы записаться:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться", callback_data="start_booking")],
            [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
        ])
    )


@dp.callback_query(F.data == "start_booking")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingState.choosing_service)
    await callback.message.edit_text("Выберите услугу:", reply_markup=services_kb())
    await callback.answer()


@dp.callback_query(F.data.startswith("svc:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)
    await state.set_state(BookingState.choosing_date)
    await callback.message.edit_text(f"✅ Услуга: *{service}*\n\nВыберите дату:", reply_markup=dates_kb(), parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    book_date = callback.data.split(":", 1)[1]
    booked = get_booked_times(book_date)
    await state.update_data(date=book_date)
    await state.set_state(BookingState.choosing_time)
    d_fmt = datetime.strptime(book_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    await callback.message.edit_text(f"📅 Дата: *{d_fmt}*\n\nВыберите время (❌ = занято):", reply_markup=times_kb(booked), parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "booked")
async def slot_taken(callback: CallbackQuery):
    await callback.answer("Это время уже занято, выберите другое.", show_alert=True)


@dp.callback_query(F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    book_time = callback.data.split(":", 1)[1]
    await state.update_data(time=book_time)
    await state.set_state(BookingState.entering_phone)
    await callback.message.edit_text(f"⏰ Время: *{book_time}*\n\nВведите ваш номер телефона:", parse_mode="Markdown")
    await callback.answer()


@dp.message(BookingState.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    data = await state.get_data()
    await state.update_data(phone=phone)
    await state.set_state(BookingState.confirming)

    d_fmt = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
    await message.answer(
        f"📋 *Подтвердите запись:*\n\n"
        f"🏢 {BUSINESS_NAME}\n"
        f"💼 Услуга: {data['service']}\n"
        f"📅 Дата: {d_fmt}\n"
        f"⏰ Время: {data['time']}\n"
        f"📞 Телефон: {phone}",
        parse_mode="Markdown",
        reply_markup=confirm_kb(),
    )


@dp.callback_query(F.data == "confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    save_booking(user.id, user.username or "", user.first_name or "", data["phone"], data["service"], data["date"], data["time"])
    await state.clear()

    d_fmt = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
    await callback.message.edit_text(
        f"✅ *Запись подтверждена!*\n\n"
        f"📅 {d_fmt} в {data['time']}\n"
        f"💼 {data['service']}\n\n"
        f"Мы свяжемся с вами по номеру {data['phone']}",
        parse_mode="Markdown",
    )

    # Notify all admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🔔 *Новая запись!*\n\n"
                f"👤 {user.first_name} (@{user.username})\n"
                f"📞 {data['phone']}\n"
                f"💼 {data['service']}\n"
                f"📅 {d_fmt} {data['time']}",
                parse_mode="Markdown",
            )
        except Exception:
            pass
    await callback.answer()


@dp.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Запись отменена.")
    await callback.answer()


@dp.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    conn = sqlite3.connect("bookings.db")
    rows = conn.execute(
        "SELECT service, date, time, status FROM bookings WHERE user_id = ? ORDER BY date DESC, time DESC LIMIT 5",
        (callback.from_user.id,)
    ).fetchall()
    conn.close()

    if not rows:
        await callback.message.edit_text("У вас нет записей.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📅 Записаться", callback_data="start_booking")]]))
    else:
        lines = ["📋 *Ваши записи:*\n"]
        for r in rows:
            d_fmt = datetime.strptime(r[1], "%Y-%m-%d").strftime("%d.%m.%Y")
            status_icon = {"pending": "🕐", "confirmed": "✅", "cancelled": "❌"}.get(r[3], "🕐")
            lines.append(f"{status_icon} {d_fmt} {r[2]} — {r[0]}")
        await callback.message.edit_text("\n".join(lines), parse_mode="Markdown")
    await callback.answer()


@dp.message(Command("bookings"))
async def cmd_bookings(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    rows = get_all_bookings(status="pending")
    if not rows:
        await message.answer("Нет активных записей.")
        return
    lines = ["📋 *Активные записи:*\n"]
    for r in rows:
        d_fmt = datetime.strptime(r[6], "%Y-%m-%d").strftime("%d.%m.%Y")
        lines.append(f"#{r[0]} | {d_fmt} {r[7]} | {r[5]} | {r[3]} ({r[4]})")
    await message.answer("\n".join(lines), parse_mode="Markdown")


async def main():
    logging.info("Booking bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

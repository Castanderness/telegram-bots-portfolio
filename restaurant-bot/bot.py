"""
Restaurant bot: menu, table booking, daily specials, admin orders view.
Sell to cafes/restaurants: $150-300 setup + $30/mo.
"""
import asyncio, os, sqlite3, logging
from datetime import date, datetime, timedelta
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
ADMIN_IDS      = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip()]
REST_NAME      = os.getenv("REST_NAME", "Ресторан «Уют»")
REST_ADDRESS   = os.getenv("REST_ADDRESS", "ул. Примерная, 1")
REST_PHONE     = os.getenv("REST_PHONE", "+7 (999) 123-45-67")
WORK_HOURS     = os.getenv("WORK_HOURS", "12:00 – 23:00")

bot = Bot(token=TELEGRAM_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

MENU = {
    "Закуски": [
        ("Брускетта с томатами",    250),
        ("Карпаччо из говядины",    490),
        ("Сырная тарелка",          580),
    ],
    "Супы": [
        ("Борщ со сметаной",        320),
        ("Крем-суп из тыквы",       290),
        ("Уха из лосося",           410),
    ],
    "Основные блюда": [
        ("Стейк рибай 250г",        1290),
        ("Паста карбонара",         490),
        ("Лосось на гриле",         890),
        ("Куриное филе в соусе",    590),
    ],
    "Десерты": [
        ("Тирамису",                350),
        ("Чизкейк Нью-Йорк",       380),
        ("Шоколадный фондан",       420),
    ],
}

def init_db():
    conn = sqlite3.connect("restaurant.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, name TEXT, phone TEXT,
        guests INTEGER, date TEXT, time TEXT,
        comment TEXT, status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit(); conn.close()

def save_booking(user_id, name, phone, guests, bdate, btime, comment=""):
    conn = sqlite3.connect("restaurant.db")
    conn.execute("INSERT INTO bookings (user_id,name,phone,guests,date,time,comment) VALUES (?,?,?,?,?,?,?)",
                 (user_id, name, phone, guests, bdate, btime, comment))
    conn.commit(); conn.close()

def get_bookings():
    conn = sqlite3.connect("restaurant.db")
    rows = conn.execute("SELECT * FROM bookings ORDER BY date,time DESC LIMIT 30").fetchall()
    conn.close(); return rows

init_db()

class BookState(StatesGroup):
    name = State(); phone = State(); guests = State()
    date = State(); time = State(); comment = State()

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Меню",          callback_data="menu")],
        [InlineKeyboardButton(text="📅 Забронировать", callback_data="book")],
        [InlineKeyboardButton(text="📞 Контакты",      callback_data="contacts")],
        [InlineKeyboardButton(text="🎯 Акции",         callback_data="specials")],
    ])

def menu_kb():
    buttons = [[InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")] for cat in MENU]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def dates_kb():
    today = date.today()
    buttons = []
    for i in range(1, 8):
        d = today + timedelta(days=i)
        buttons.append([InlineKeyboardButton(text=d.strftime("%d.%m (%A)").replace("Monday","Пн").replace("Tuesday","Вт").replace("Wednesday","Ср").replace("Thursday","Чт").replace("Friday","Пт").replace("Saturday","Сб").replace("Sunday","Вс"),
                                             callback_data=f"bdate:{d.isoformat()}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def times_kb():
    times = ["12:00","13:00","14:00","15:00","17:00","18:00","19:00","20:00","21:00"]
    rows = []
    row = []
    for t in times:
        row.append(InlineKeyboardButton(text=t, callback_data=f"btime:{t}"))
        if len(row) == 3: rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

@dp.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(f"Добро пожаловать в {REST_NAME}! 🍽️\n\nВыберите действие:", reply_markup=main_kb())

@dp.callback_query(F.data == "menu")
async def show_menu(cb: CallbackQuery):
    await cb.message.edit_text("📋 Выберите раздел меню:", reply_markup=menu_kb())
    await cb.answer()

@dp.callback_query(F.data.startswith("cat:"))
async def show_category(cb: CallbackQuery):
    cat = cb.data.split(":", 1)[1]
    items = MENU.get(cat, [])
    lines = [f"*{cat}*\n"]
    for name, price in items:
        lines.append(f"• {name} — {price} руб.")
    buttons = [[InlineKeyboardButton(text="⬅️ К меню", callback_data="menu")]]
    await cb.message.edit_text("\n".join(lines), parse_mode="Markdown",
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery):
    await cb.message.edit_text("Выберите действие:", reply_markup=main_kb())
    await cb.answer()

@dp.callback_query(F.data == "contacts")
async def contacts(cb: CallbackQuery):
    text = (f"📞 *Контакты {REST_NAME}*\n\n"
            f"📍 {REST_ADDRESS}\n"
            f"☎️ {REST_PHONE}\n"
            f"🕐 {WORK_HOURS}")
    await cb.message.edit_text(text, parse_mode="Markdown",
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]]))
    await cb.answer()

@dp.callback_query(F.data == "specials")
async def specials(cb: CallbackQuery):
    await cb.message.edit_text(
        "🎯 *Акции и спецпредложения*\n\n"
        "🍷 Бизнес-ланч 12:00–15:00 — 450 руб.\n"
        "🥂 Счастливые часы 17:00–19:00 — -20% на напитки\n"
        "👨‍👩‍👧 Детское меню — бесплатно до 6 лет\n\n"
        "Забронируй столик прямо сейчас! 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Забронировать", callback_data="book")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")],
        ])
    )
    await cb.answer()

@dp.callback_query(F.data == "book")
async def book_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(BookState.name)
    await cb.message.edit_text("📅 *Бронирование столика*\n\nВведите ваше имя:")
    await cb.answer()

@dp.message(BookState.name)
async def book_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(BookState.phone)
    await msg.answer("📞 Введите номер телефона:")

@dp.message(BookState.phone)
async def book_phone(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    await state.set_state(BookState.guests)
    await msg.answer("👥 Сколько гостей? (введите число)")

@dp.message(BookState.guests)
async def book_guests(msg: Message, state: FSMContext):
    try:
        guests = int(msg.text)
    except ValueError:
        await msg.answer("Введите число, например: 2")
        return
    await state.update_data(guests=guests)
    await state.set_state(BookState.date)
    await msg.answer("📅 Выберите дату:", reply_markup=dates_kb())

@dp.callback_query(F.data.startswith("bdate:"))
async def book_date(cb: CallbackQuery, state: FSMContext):
    await state.update_data(date=cb.data.split(":")[1])
    await state.set_state(BookState.time)
    await cb.message.edit_text("⏰ Выберите время:", reply_markup=times_kb())
    await cb.answer()

@dp.callback_query(F.data.startswith("btime:"))
async def book_time(cb: CallbackQuery, state: FSMContext):
    await state.update_data(time=cb.data.split(":")[1])
    await state.set_state(BookState.comment)
    await cb.message.edit_text("💬 Пожелания (аллергии, особые требования) или /skip:")
    await cb.answer()

@dp.message(BookState.comment)
async def book_comment(msg: Message, state: FSMContext):
    comment = "" if msg.text == "/skip" else msg.text
    data = await state.get_data()
    await state.clear()
    save_booking(msg.from_user.id, data["name"], data["phone"],
                 data["guests"], data["date"], data["time"], comment)
    d_fmt = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
    await msg.answer(
        f"✅ *Бронирование принято!*\n\n"
        f"👤 {data['name']}\n"
        f"📅 {d_fmt} в {data['time']}\n"
        f"👥 {data['guests']} гостей\n"
        f"📞 {data['phone']}\n\n"
        f"Ждём вас в {REST_NAME}! 🍽️",
        parse_mode="Markdown"
    )
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(aid,
                f"🔔 Новое бронирование!\n{data['name']} | {data['phone']}\n"
                f"{d_fmt} {data['time']} | {data['guests']} чел.\n{comment}")
        except Exception: pass

@dp.message(Command("bookings"))
async def admin_bookings(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    rows = get_bookings()
    if not rows: await msg.answer("Нет бронирований."); return
    lines = ["📋 *Последние бронирования:*\n"]
    for r in rows[:10]:
        d = datetime.strptime(r[6], "%Y-%m-%d").strftime("%d.%m")
        lines.append(f"#{r[0]} {d} {r[7]} | {r[2]} | {r[4]} чел. | {r[3]}")
    await msg.answer("\n".join(lines), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

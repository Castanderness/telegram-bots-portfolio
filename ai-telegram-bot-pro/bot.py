import asyncio
import os
import logging
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message, InlineKeyboardMarkup, InlineKeyboardButton,
                           CallbackQuery, PreCheckoutQuery)
from aiogram.fsm.storage.memory import MemoryStorage
from anthropic import Anthropic
from dotenv import load_dotenv

import database as db
from payments import send_premium_invoice, process_pre_checkout, process_successful_payment

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant. Be concise and friendly. Answer in the language the user writes in.")
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "20"))

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
client = Anthropic(api_key=ANTHROPIC_API_KEY)

db.init_db()


def premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Купить Premium — $15/мес", callback_data="buy_premium")],
        [InlineKeyboardButton(text="📊 Мой статус", callback_data="my_status")],
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👑 Выдать Premium", callback_data="admin_grant")],
    ])


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = db.get_or_create_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name or "")
    is_admin = message.from_user.id in ADMIN_IDS

    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я AI-ассистент на базе Claude.\n"
        f"Бесплатно: {FREE_DAILY_LIMIT} сообщений в день\n"
        f"Premium: безлимит + приоритет\n\n"
        f"Задай любой вопрос!"
    )
    kb = admin_keyboard() if is_admin else premium_keyboard()
    await message.answer(text, reply_markup=kb)


@dp.message(Command("status"))
async def cmd_status(message: Message):
    db.reset_daily_if_needed(message.from_user.id)
    user = db.get_or_create_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name or "")
    msgs_today = db.get_msg_count_today(message.from_user.id)
    premium = db.is_premium(message.from_user.id)

    status = "⭐ Premium" if premium else f"🆓 Free ({msgs_today}/{FREE_DAILY_LIMIT} сегодня)"
    await message.answer(
        f"📊 Твой статус: {status}\n"
        f"📨 Всего сообщений: {user['msgs_total']}\n"
        f"📅 Сегодня: {msgs_today}",
        reply_markup=premium_keyboard() if not premium else None,
    )


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    # Clear history by inserting a sentinel — simplest approach with SQLite is just to ignore old msgs
    await message.answer("✅ История диалога очищена.")


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    stats = db.get_stats()
    await message.answer(
        f"🔧 Панель администратора\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"⭐ Premium: {stats['premium_users']}\n"
        f"📨 Всего сообщений: {stats['total_msgs']}\n"
        f"🟢 Активны сегодня: {stats['active_today']}",
        reply_markup=admin_keyboard(),
    )


@dp.message(Command("grant"))
async def cmd_grant(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /grant <user_id> [дней=30]")
        return
    try:
        target_id = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 30
    except ValueError:
        await message.answer("Неверный формат. /grant <user_id> [дней]")
        return

    until = (date.today() + timedelta(days=days)).isoformat()
    db.set_premium(target_id, until)
    await message.answer(f"✅ Пользователю {target_id} выдан Premium до {until}")


@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: CallbackQuery):
    await callback.message.answer(
        "⭐ *Premium подписка*\n\n"
        "✅ Безлимитные сообщения\n"
        "✅ История диалога 100 сообщений\n\n"
        "Выбери тариф:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ 150 Stars — 1 месяц", callback_data="pay_stars_150")],
            [InlineKeyboardButton(text="⭐ 350 Stars — 3 месяца", callback_data="pay_stars_350")],
        ])
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("pay_stars_"))
async def cb_pay_stars(callback: CallbackQuery):
    stars = int(callback.data.split("_")[2])
    await send_premium_invoice(callback.message, stars)
    await callback.answer()


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await process_pre_checkout(query)


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    await process_successful_payment(message)


@dp.callback_query(F.data == "my_status")
async def cb_my_status(callback: CallbackQuery):
    await cmd_status(callback.message)
    await callback.answer()


@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    stats = db.get_stats()
    await callback.message.answer(
        f"📊 Статистика бота\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"⭐ Premium: {stats['premium_users']}\n"
        f"📨 Сообщений: {stats['total_msgs']}\n"
        f"🟢 Сегодня активны: {stats['active_today']}"
    )
    await callback.answer()


@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    db.get_or_create_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
    db.reset_daily_if_needed(user_id)

    # Check free limit
    if not db.is_premium(user_id):
        msgs_today = db.get_msg_count_today(user_id)
        if msgs_today >= FREE_DAILY_LIMIT:
            await message.answer(
                f"⛔ Лимит {FREE_DAILY_LIMIT} сообщений в день исчерпан.\n\n"
                f"Купи Premium для безлимитного доступа 👇",
                reply_markup=premium_keyboard(),
            )
            return

    history = db.get_history(user_id, limit=20)
    history.append({"role": "user", "content": message.text})

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text
    except Exception as e:
        logging.error(f"Claude API error: {e}")
        reply = "Произошла ошибка. Попробуйте ещё раз через минуту."

    db.save_message(user_id, "user", message.text)
    db.save_message(user_id, "assistant", reply)
    db.increment_message_count(user_id)

    await message.answer(reply)


async def main():
    logging.info("Pro bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

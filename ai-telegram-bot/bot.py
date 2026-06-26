import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful assistant. Be concise and friendly. Answer in the language the user writes in."
)
MAX_HISTORY = 20

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
client = Anthropic(api_key=ANTHROPIC_API_KEY)

conversations: dict[int, list] = {}


@dp.message(CommandStart())
async def cmd_start(message: Message):
    conversations[message.from_user.id] = []
    await message.answer(
        "👋 Привет! Я AI-ассистент на базе Claude.\n\n"
        "Задай любой вопрос — отвечу мгновенно.\n\n"
        "/clear — очистить историю диалога\n"
        "/help — помощь"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Я умею:\n"
        "• Отвечать на любые вопросы\n"
        "• Писать тексты, код, письма\n"
        "• Объяснять сложные темы\n"
        "• Переводить на любой язык\n\n"
        "Просто напишите сообщение!"
    )


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    conversations[message.from_user.id] = []
    await message.answer("✅ История диалога очищена. Начинаем заново!")


@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": message.text})

    if len(conversations[user_id]) > MAX_HISTORY:
        conversations[user_id] = conversations[user_id][-MAX_HISTORY:]

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Haiku — дешевле, быстрее
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversations[user_id],
        )
        reply = response.content[0].text
    except Exception as e:
        logging.error(f"Claude API error: {e}")
        reply = "Произошла ошибка. Попробуйте ещё раз."

    conversations[user_id].append({"role": "assistant", "content": reply})
    await message.answer(reply)


async def main():
    logging.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

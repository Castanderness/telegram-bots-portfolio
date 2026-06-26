"""
Survey/feedback bot: sends questions, collects answers, saves to Excel.
Sell to businesses: $60-120 + $20/mo.
"""
import asyncio, os, json, logging
from pathlib import Path
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import openpyxl
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS      = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip()]

bot = Bot(token=TELEGRAM_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ── Customize your survey here ────────────────────────────────────────────────
SURVEY_TITLE = "Опрос качества обслуживания"
QUESTIONS = [
    {"id": "q1", "text": "Оцените качество обслуживания:", "type": "rating"},
    {"id": "q2", "text": "Оцените качество продукта:", "type": "rating"},
    {"id": "q3", "text": "Порекомендуете нас друзьям?", "type": "choice",
     "options": ["Да, точно", "Возможно", "Нет"]},
    {"id": "q4", "text": "Что можно улучшить? (напишите или пропустите /skip)", "type": "text"},
]
RESULTS_FILE = Path(__file__).parent / "survey_results.xlsx"
# ──────────────────────────────────────────────────────────────────────────────

class SurveyState(StatesGroup):
    answering = State()


def rating_kb(q_id: str) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=str(i) + ("⭐" if i == 5 else ""),
                                     callback_data=f"r:{q_id}:{i}") for i in range(1, 6)]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def choice_kb(q_id: str, options: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=opt, callback_data=f"c:{q_id}:{i}")]
               for i, opt in enumerate(options)]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def save_to_excel(user_id: int, username: str, answers: dict):
    if RESULTS_FILE.exists():
        wb = openpyxl.load_workbook(RESULTS_FILE)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Результаты"
        headers = ["Дата", "User ID", "Username"] + [q["id"] for q in QUESTIONS]
        ws.append(headers)

    row = [datetime.now().strftime("%d.%m.%Y %H:%M"), user_id, username or ""]
    for q in QUESTIONS:
        row.append(answers.get(q["id"], "—"))
    ws.append(row)
    wb.save(RESULTS_FILE)


async def ask_question(msg_or_cb, q_index: int, state: FSMContext):
    q = QUESTIONS[q_index]
    await state.update_data(current_q=q_index)

    text = f"*Вопрос {q_index+1}/{len(QUESTIONS)}*\n\n{q['text']}"

    if q["type"] == "rating":
        kb = rating_kb(q["id"])
        if hasattr(msg_or_cb, "message"):
            await msg_or_cb.message.answer(text, parse_mode="Markdown", reply_markup=kb)
        else:
            await msg_or_cb.answer(text, parse_mode="Markdown", reply_markup=kb)
    elif q["type"] == "choice":
        kb = choice_kb(q["id"], q["options"])
        if hasattr(msg_or_cb, "message"):
            await msg_or_cb.message.answer(text, parse_mode="Markdown", reply_markup=kb)
        else:
            await msg_or_cb.answer(text, parse_mode="Markdown", reply_markup=kb)
    else:
        if hasattr(msg_or_cb, "message"):
            await msg_or_cb.message.answer(text, parse_mode="Markdown")
        else:
            await msg_or_cb.answer(text, parse_mode="Markdown")


@dp.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        f"Добро пожаловать! 👋\n\n"
        f"Это займёт 1–2 минуты.\n\n"
        f"Нажмите кнопку ниже чтобы начать *{SURVEY_TITLE}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📝 Начать опрос", callback_data="start_survey")
        ]])
    )


@dp.callback_query(F.data == "start_survey")
async def survey_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(SurveyState.answering)
    await state.update_data(answers={})
    await ask_question(cb, 0, state)
    await cb.answer()


async def next_or_finish(source, state: FSMContext):
    data = await state.get_data()
    q_index = data["current_q"] + 1

    if q_index >= len(QUESTIONS):
        # Survey complete
        answers = data["answers"]
        user = source.from_user if hasattr(source, "from_user") else source.message.from_user
        save_to_excel(user.id, user.username, answers)
        await state.clear()

        msg_target = source if isinstance(source, Message) else source.message
        await msg_target.answer("✅ *Спасибо за ваши ответы!*\n\nВаше мнение очень важно для нас.", parse_mode="Markdown")

        for aid in ADMIN_IDS:
            try:
                lines = [f"📊 Новый ответ от @{user.username or user.id}"]
                for q in QUESTIONS:
                    lines.append(f"{q['id']}: {answers.get(q['id'], '—')}")
                await bot.send_message(aid, "\n".join(lines))
            except Exception: pass
    else:
        await ask_question(source, q_index, state)


@dp.callback_query(F.data.startswith("r:"))
async def rating_answer(cb: CallbackQuery, state: FSMContext):
    _, q_id, score = cb.data.split(":")
    data = await state.get_data()
    answers = data.get("answers", {})
    answers[q_id] = int(score)
    await state.update_data(answers=answers)
    await cb.message.edit_reply_markup()
    await cb.answer(f"Ответ: {score} ⭐")
    await next_or_finish(cb, state)


@dp.callback_query(F.data.startswith("c:"))
async def choice_answer(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    q_id, opt_idx = parts[1], int(parts[2])
    q = next(q for q in QUESTIONS if q["id"] == q_id)
    chosen = q["options"][opt_idx]
    data = await state.get_data()
    answers = data.get("answers", {})
    answers[q_id] = chosen
    await state.update_data(answers=answers)
    await cb.message.edit_reply_markup()
    await cb.answer(f"Выбрано: {chosen}")
    await next_or_finish(cb, state)


@dp.message(SurveyState.answering)
async def text_answer(msg: Message, state: FSMContext):
    data = await state.get_data()
    q_index = data["current_q"]
    q = QUESTIONS[q_index]
    if q["type"] == "text":
        answers = data.get("answers", {})
        answers[q["id"]] = "" if msg.text == "/skip" else msg.text
        await state.update_data(answers=answers)
        await next_or_finish(msg, state)


@dp.message(Command("results"))
async def admin_results(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    if RESULTS_FILE.exists():
        await msg.answer_document(RESULTS_FILE.open("rb"), caption="📊 Результаты опроса")
    else:
        await msg.answer("Пока нет ответов.")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

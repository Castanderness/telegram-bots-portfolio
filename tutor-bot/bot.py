"""
English tutor bot. Teaches vocabulary, grammar, runs quizzes.
No Anthropic needed — works standalone.
Sell: $80-150 per bot, $15/mo subscriptions.
"""
import asyncio, os, random, json, logging
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp  = Dispatcher(storage=MemoryStorage())

WORDS = [
    ("apple",       "яблоко"),
    ("book",        "книга"),
    ("car",         "машина"),
    ("house",       "дом"),
    ("water",       "вода"),
    ("friend",      "друг"),
    ("time",        "время"),
    ("work",        "работа"),
    ("money",       "деньги"),
    ("city",        "город"),
    ("beautiful",   "красивый"),
    ("important",   "важный"),
    ("difficult",   "сложный"),
    ("successful",  "успешный"),
    ("opportunity", "возможность"),
    ("knowledge",   "знание"),
    ("experience",  "опыт"),
    ("business",    "бизнес"),
    ("development", "развитие"),
    ("technology",  "технология"),
]

PHRASES = [
    ("How are you?",          "Как дела?"),
    ("Nice to meet you.",     "Приятно познакомиться."),
    ("What time is it?",      "Который час?"),
    ("I need help.",          "Мне нужна помощь."),
    ("How much does it cost?","Сколько это стоит?"),
    ("Where is the exit?",    "Где выход?"),
    ("Can you help me?",      "Ты можешь мне помочь?"),
    ("I don't understand.",   "Я не понимаю."),
    ("Please speak slowly.",  "Говори, пожалуйста, медленнее."),
    ("Thank you very much.",  "Большое спасибо."),
]

GRAMMAR_TIPS = [
    "**Present Simple** используется для регулярных действий.\n_I work every day._ (Я работаю каждый день.)",
    "**Past Simple** для завершённых действий в прошлом.\n_I worked yesterday._ (Я работал вчера.)",
    "**Future Simple** с will для будущего.\n_I will work tomorrow._ (Я буду работать завтра.)",
    "**Present Continuous** для действий прямо сейчас.\n_I am working now._ (Я работаю сейчас.)",
    "**Present Perfect** когда важен результат, а не время.\n_I have finished._ (Я закончил.)",
    "**Артикль 'a'** — неопределённый, для любого предмета: _a book_.",
    "**Артикль 'the'** — определённый, конкретный предмет: _the book on the table_.",
    "**Much/Many**: much + неисчисляемое (_much water_), many + исчисляемое (_many books_).",
]

class QuizState(StatesGroup):
    answering = State()


def quiz_kb(correct: str, all_words: list) -> InlineKeyboardMarkup:
    others = [w for w in all_words if w[0] != correct]
    options = random.sample(others, min(3, len(others)))
    options.append(next(w for w in all_words if w[0] == correct))
    random.shuffle(options)
    buttons = [[InlineKeyboardButton(text=o[1], callback_data=f"ans:{o[0]}:{correct}")] for o in options]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Я твой репетитор по английскому 🇬🇧\n\n"
        "/word — слово дня\n"
        "/phrase — фраза дня\n"
        "/quiz — тест на слова\n"
        "/grammar — грамматика\n"
        "/lesson — мини-урок"
    )

@dp.message(Command("word"))
async def word_of_day(message: Message):
    eng, rus = random.choice(WORDS)
    await message.answer(f"📖 *Слово дня*\n\n🇬🇧 *{eng}*\n🇷🇺 {rus}\n\nПопробуй составить предложение!", parse_mode="Markdown")

@dp.message(Command("phrase"))
async def phrase_of_day(message: Message):
    eng, rus = random.choice(PHRASES)
    await message.answer(f"💬 *Фраза дня*\n\n🇬🇧 *{eng}*\n🇷🇺 {rus}\n\nПовтори вслух 3 раза!", parse_mode="Markdown")

@dp.message(Command("grammar"))
async def grammar(message: Message):
    tip = random.choice(GRAMMAR_TIPS)
    await message.answer(f"📚 *Грамматика*\n\n{tip}", parse_mode="Markdown")

@dp.message(Command("quiz"))
async def quiz(message: Message, state: FSMContext):
    word = random.choice(WORDS)
    await state.update_data(correct=word[0])
    await state.set_state(QuizState.answering)
    await message.answer(
        f"❓ Как переводится слово:\n\n🇬🇧 *{word[0]}*",
        parse_mode="Markdown",
        reply_markup=quiz_kb(word[0], WORDS)
    )

@dp.callback_query(F.data.startswith("ans:"))
async def check_answer(cb: CallbackQuery, state: FSMContext):
    _, chosen, correct = cb.data.split(":")
    if chosen == correct:
        await cb.message.edit_text(f"✅ Правильно! *{correct}* = {next(w[1] for w in WORDS if w[0]==correct)}", parse_mode="Markdown")
    else:
        right = next(w[1] for w in WORDS if w[0]==correct)
        await cb.message.edit_text(f"❌ Неверно.\nПравильный ответ: *{correct}* = {right}", parse_mode="Markdown")
    await state.clear()
    await cb.answer()

@dp.message(Command("lesson"))
async def lesson(message: Message):
    words = random.sample(WORDS, 5)
    lines = ["📝 *Мини-урок: 5 слов*\n"]
    for eng, rus in words:
        lines.append(f"• *{eng}* — {rus}")
    lines.append("\n/quiz — проверь себя!")
    await message.answer("\n".join(lines), parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

"""
Vacancy channel bot: parses hh.ru API and posts new vacancies to Telegram channel.
Runs every 2 hours. Tracks posted IDs to avoid duplicates.
Sell: $80-150 setup per niche.
"""
import asyncio, os, json, logging
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN  = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SEARCH_QUERY = os.getenv("VACANCY_QUERY", "Python разработчик")
CITY_ID    = os.getenv("CITY_ID", "1")  # 1=Москва, 2=СПб, 113=Россия
SALARY_FROM = int(os.getenv("SALARY_FROM", "0"))

bot = Bot(token=BOT_TOKEN)
POSTED_FILE = Path(__file__).parent / "posted_ids.json"


def load_posted() -> set:
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()


def save_posted(ids: set):
    POSTED_FILE.write_text(json.dumps(list(ids)))


def fetch_vacancies() -> list[dict]:
    params = {
        "text": SEARCH_QUERY,
        "area": CITY_ID,
        "per_page": 20,
        "order_by": "publication_time",
        "search_field": "name",
    }
    if SALARY_FROM > 0:
        params["salary"] = SALARY_FROM
        params["only_with_salary"] = "true"

    r = requests.get("https://api.hh.ru/vacancies", params=params,
                     headers={"User-Agent": "VacancyBot/1.0"}, timeout=15)
    return r.json().get("items", [])


def format_vacancy(v: dict) -> str:
    name     = v.get("name", "—")
    company  = v.get("employer", {}).get("name", "—")
    salary   = v.get("salary") or {}
    sal_from = salary.get("from")
    sal_to   = salary.get("to")
    currency = salary.get("currency", "RUR")
    area     = v.get("area", {}).get("name", "—")
    url      = v.get("alternate_url", "")

    if sal_from and sal_to:
        sal_str = f"{sal_from:,}–{sal_to:,} {currency}"
    elif sal_from:
        sal_str = f"от {sal_from:,} {currency}"
    elif sal_to:
        sal_str = f"до {sal_to:,} {currency}"
    else:
        sal_str = "не указана"

    return (
        f"💼 *{name}*\n"
        f"🏢 {company}\n"
        f"📍 {area}\n"
        f"💰 {sal_str}\n"
        f"🔗 [Открыть вакансию]({url})"
    )


async def check_and_post():
    posted = load_posted()
    vacancies = fetch_vacancies()
    new_count = 0

    for v in vacancies:
        vid = v["id"]
        if vid in posted:
            continue
        try:
            text = format_vacancy(v)
            await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown",
                                   disable_web_page_preview=True)
            posted.add(vid)
            new_count += 1
            await asyncio.sleep(2)
        except Exception as e:
            logging.error(f"Failed to post {vid}: {e}")

    save_posted(posted)
    logging.info(f"Posted {new_count} new vacancies")


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_and_post, "interval", hours=2)
    scheduler.start()
    await check_and_post()  # run immediately on start
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

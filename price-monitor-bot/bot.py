"""
Avito price monitor: tracks listings by search query,
posts new and price-drop items to Telegram channel.
Sell: $80-150 setup per category.
"""
import asyncio, os, json, logging, re
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
from bs4 import BeautifulSoup
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN    = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID   = os.getenv("CHANNEL_ID")
SEARCH_URL   = os.getenv("AVITO_URL", "https://www.avito.ru/rossiya?q=iphone+15&s=104")
MAX_PRICE    = int(os.getenv("MAX_PRICE", "999999"))
CHECK_MINS   = int(os.getenv("CHECK_INTERVAL_MINS", "30"))

bot = Bot(token=BOT_TOKEN)
SEEN_FILE = Path(__file__).parent / "seen_items.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
}


def load_seen() -> dict:
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    return {}


def save_seen(data: dict):
    SEEN_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def parse_avito(url: str) -> list[dict]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for card in soup.select("[data-marker='item']"):
            try:
                link_el  = card.select_one("[data-marker='item-title']")
                price_el = card.select_one("[data-marker='item-price']")
                if not link_el or not price_el:
                    continue
                title = link_el.get_text(strip=True)
                href  = "https://www.avito.ru" + link_el.get("href", "")
                item_id = re.search(r"_(\d+)$", href)
                item_id = item_id.group(1) if item_id else href[-10:]
                price_text = price_el.get_text(strip=True)
                price_num  = int(re.sub(r"\D", "", price_text) or "0")
                if price_num <= MAX_PRICE:
                    items.append({"id": item_id, "title": title,
                                  "price": price_num, "price_str": price_text, "url": href})
            except Exception:
                pass
        return items
    except Exception as e:
        logging.error(f"Parse error: {e}")
        return []


async def check_and_post():
    seen = load_seen()
    items = parse_avito(SEARCH_URL)
    posted = 0

    for item in items:
        iid = item["id"]
        if iid in seen:
            old_price = seen[iid]
            if item["price"] < old_price * 0.95:  # price dropped 5%+
                drop = old_price - item["price"]
                text = (
                    f"📉 *Снижение цены!*\n\n"
                    f"🏷️ {item['title']}\n"
                    f"💰 ~~{old_price:,}~~ → *{item['price']:,} руб* (−{drop:,})\n"
                    f"🔗 [Смотреть]({item['url']})"
                )
                await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")
                posted += 1
        else:
            text = (
                f"🆕 *Новое объявление*\n\n"
                f"🏷️ {item['title']}\n"
                f"💰 {item['price_str']}\n"
                f"🔗 [Смотреть]({item['url']})"
            )
            await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")
            posted += 1

        seen[iid] = item["price"]
        if posted > 0:
            await asyncio.sleep(1.5)

    save_seen(seen)
    logging.info(f"Posted {posted} items")


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_and_post, "interval", minutes=CHECK_MINS)
    scheduler.start()
    await check_and_post()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

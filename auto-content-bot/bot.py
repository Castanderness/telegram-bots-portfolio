"""
Auto-content Telegram channel bot.
Posts crypto news + tips daily at scheduled times.
Sell as a service: $50-100 setup + $20/mo.
"""
import asyncio, os, logging, random
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN  = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")   # e.g. @mychannel or -100123456789

bot = Bot(token=BOT_TOKEN)

CRYPTO_TIPS = [
    "Bitcoin был создан в 2009 году анонимным автором под псевдонимом Сатоши Накамото.",
    "Ethereum позволяет создавать смарт-контракты — программы, работающие прямо в блокчейне.",
    "Не храни все средства на бирже — используй аппаратный кошелёк для больших сумм.",
    "DCA (усреднение долларовой стоимости) — лучшая стратегия для новичков.",
    "DYOR — Do Your Own Research. Всегда проверяй информацию перед инвестицией.",
    "Рыночная капитализация = цена × количество монет в обращении.",
    "Halving Bitcoin происходит каждые ~4 года и сокращает награду майнеров вдвое.",
    "Gas в Ethereum — плата за вычисления в сети. Чем сложнее операция, тем выше gas.",
    "Stablecoins (USDT, USDC) привязаны к доллару и защищают от волатильности.",
    "NFT — уникальные цифровые активы, подтверждённые блокчейном.",
]

MORNING_GREETINGS = [
    "Доброе утро! Крипторынок не спит — и мы тоже 🌅",
    "Утро начинается с проверки портфеля! Что там у нас сегодня? 📊",
    "Новый день — новые возможности на рынке 🚀",
]

EVENING_FACTS = [
    "💡 Факт дня: {tip}",
    "🧠 Знаете ли вы? {tip}",
    "📚 Полезно знать: {tip}",
]


async def post_morning():
    text = (
        f"{random.choice(MORNING_GREETINGS)}\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"Следите за обновлениями!"
    )
    await bot.send_message(CHANNEL_ID, text)
    logging.info("Morning post sent")


async def post_tip():
    tip = random.choice(CRYPTO_TIPS)
    template = random.choice(EVENING_FACTS)
    text = template.format(tip=tip)
    await bot.send_message(CHANNEL_ID, text)
    logging.info("Tip post sent")


async def post_price_update():
    import requests
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,solana,the-open-network&vs_currencies=usd&include_24hr_change=true",
            timeout=10
        )
        d = r.json()
        lines = ["📊 Цены крипты:\n"]
        symbols = [("bitcoin","BTC"),("ethereum","ETH"),("solana","SOL"),("the-open-network","TON")]
        for cid, sym in symbols:
            if cid in d:
                price  = d[cid]["usd"]
                change = d[cid].get("usd_24h_change", 0)
                arrow  = "🟢" if change >= 0 else "🔴"
                fmt    = f"${price:,.0f}" if price > 100 else f"${price:.3f}"
                lines.append(f"{arrow} {sym}: {fmt}  ({change:+.1f}%)")
        await bot.send_message(CHANNEL_ID, "\n".join(lines))
        logging.info("Price update sent")
    except Exception as e:
        logging.error(f"Price update failed: {e}")


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(post_morning,      "cron", hour=9,  minute=0)
    scheduler.add_job(post_price_update, "cron", hour=12, minute=0)
    scheduler.add_job(post_tip,          "cron", hour=18, minute=0)
    scheduler.add_job(post_price_update, "cron", hour=21, minute=0)
    scheduler.start()
    logging.info("Auto-content bot started")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

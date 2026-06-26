"""
Crypto price alert bot.
Users set price targets — bot notifies when hit.
Sell to traders for $100-200 + $20/mo hosting.
"""
import asyncio
import os
import json
import logging
import sqlite3
from datetime import datetime

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SEC", "60"))

SUPPORTED_COINS = ["BTC", "ETH", "SOL", "BNB", "TON", "USDT", "XRP", "DOGE", "ADA", "AVAX"]

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# --- Database ---
def init_db():
    conn = sqlite3.connect("alerts.db")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alerts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            coin       TEXT,
            direction  TEXT,
            target     REAL,
            active     INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            user_id INTEGER,
            coin    TEXT,
            PRIMARY KEY (user_id, coin)
        );
    """)
    conn.commit()
    conn.close()


def add_alert(user_id: int, coin: str, direction: str, target: float):
    conn = sqlite3.connect("alerts.db")
    conn.execute("INSERT INTO alerts (user_id, coin, direction, target) VALUES (?,?,?,?)",
                 (user_id, coin, direction, target))
    conn.commit()
    conn.close()


def get_user_alerts(user_id: int) -> list:
    conn = sqlite3.connect("alerts.db")
    rows = conn.execute(
        "SELECT id, coin, direction, target FROM alerts WHERE user_id=? AND active=1 ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_all_active_alerts() -> list:
    conn = sqlite3.connect("alerts.db")
    rows = conn.execute(
        "SELECT id, user_id, coin, direction, target FROM alerts WHERE active=1"
    ).fetchall()
    conn.close()
    return rows


def deactivate_alert(alert_id: int):
    conn = sqlite3.connect("alerts.db")
    conn.execute("UPDATE alerts SET active=0 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()


def delete_alert(alert_id: int, user_id: int):
    conn = sqlite3.connect("alerts.db")
    conn.execute("DELETE FROM alerts WHERE id=? AND user_id=?", (alert_id, user_id))
    conn.commit()
    conn.close()


init_db()

# Price cache to avoid hammering API
_price_cache: dict[str, tuple[float, float]] = {}  # coin -> (price, timestamp)


def get_prices(coins: list[str]) -> dict[str, float]:
    """Fetch prices from CoinGecko (free, no API key needed)."""
    ids_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
        "TON": "the-open-network", "USDT": "tether", "XRP": "ripple",
        "DOGE": "dogecoin", "ADA": "cardano", "AVAX": "avalanche-2",
    }
    needed = [ids_map[c] for c in coins if c in ids_map]
    if not needed:
        return {}
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ",".join(needed), "vs_currencies": "usd"},
            timeout=10,
        )
        data = resp.json()
        reverse = {v: k for k, v in ids_map.items()}
        return {reverse[cid]: v["usd"] for cid, v in data.items() if cid in reverse}
    except Exception as e:
        logging.warning(f"Price fetch error: {e}")
        return {}


# --- FSM ---
class AlertState(StatesGroup):
    choosing_coin = State()
    choosing_direction = State()
    entering_price = State()


# --- Keyboards ---
def coins_kb() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, coin in enumerate(SUPPORTED_COINS):
        row.append(InlineKeyboardButton(text=coin, callback_data=f"coin:{coin}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def direction_kb(coin: str) -> InlineKeyboardMarkup:
    prices = get_prices([coin])
    price_str = f"${prices[coin]:,.2f}" if coin in prices else "..."
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📈 Выше цены  (сейчас {price_str})", callback_data="dir:above")],
        [InlineKeyboardButton(text=f"📉 Ниже цены  (сейчас {price_str})", callback_data="dir:below")],
    ])


# --- Handlers ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "📊 *Crypto Alert Bot*\n\n"
        "Получай уведомления когда крипта достигнет нужной цены.\n\n"
        "/alert — создать алерт\n"
        "/myalerts — мои алерты\n"
        "/price — текущие цены",
        parse_mode="Markdown",
    )


@dp.message(Command("price"))
async def cmd_price(message: Message):
    prices = get_prices(SUPPORTED_COINS)
    if not prices:
        await message.answer("Не удалось получить цены, попробуйте позже.")
        return
    lines = ["💹 *Текущие цены (USD):*\n"]
    for coin in SUPPORTED_COINS:
        if coin in prices:
            p = prices[coin]
            fmt = f"${p:,.0f}" if p > 100 else f"${p:.4f}"
            lines.append(f"`{coin:<6}` {fmt}")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("alert"))
async def cmd_alert(message: Message, state: FSMContext):
    await state.set_state(AlertState.choosing_coin)
    await message.answer("Выберите монету для алерта:", reply_markup=coins_kb())


@dp.callback_query(F.data.startswith("coin:"))
async def choose_coin(callback: CallbackQuery, state: FSMContext):
    coin = callback.data.split(":")[1]
    await state.update_data(coin=coin)
    await state.set_state(AlertState.choosing_direction)
    await callback.message.edit_text(
        f"*{coin}* — уведомить когда цена:",
        reply_markup=direction_kb(coin),
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("dir:"))
async def choose_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[1]
    await state.update_data(direction=direction)
    data = await state.get_data()
    coin = data["coin"]
    dir_text = "поднимется выше" if direction == "above" else "упадёт ниже"
    await state.set_state(AlertState.entering_price)
    await callback.message.edit_text(
        f"Введите целевую цену в USD для *{coin}* (уведомить когда {dir_text}):\n\nПример: `65000`",
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.message(AlertState.entering_price)
async def enter_price(message: Message, state: FSMContext):
    try:
        target = float(message.text.replace(",", "").replace("$", "").strip())
    except ValueError:
        await message.answer("Неверный формат. Введите число, например: `65000`", parse_mode="Markdown")
        return

    data = await state.get_data()
    await state.clear()
    add_alert(message.from_user.id, data["coin"], data["direction"], target)
    dir_text = "поднимется выше" if data["direction"] == "above" else "упадёт ниже"
    await message.answer(
        f"✅ Алерт создан!\n\n"
        f"🪙 {data['coin']}\n"
        f"🎯 Уведомить когда цена {dir_text} *${target:,.2f}*",
        parse_mode="Markdown",
    )


@dp.message(Command("myalerts"))
async def cmd_myalerts(message: Message):
    alerts = get_user_alerts(message.from_user.id)
    if not alerts:
        await message.answer("У вас нет активных алертов.\n\nСоздать: /alert")
        return
    lines = ["🔔 *Ваши активные алерты:*\n"]
    buttons = []
    for a in alerts:
        aid, coin, direction, target = a
        icon = "📈" if direction == "above" else "📉"
        lines.append(f"`#{aid}` {icon} {coin} {'>' if direction == 'above' else '<'} ${target:,.2f}")
        buttons.append([InlineKeyboardButton(text=f"❌ Удалить #{aid}", callback_data=f"del:{aid}")])
    await message.answer(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@dp.callback_query(F.data.startswith("del:"))
async def delete_alert_cb(callback: CallbackQuery):
    alert_id = int(callback.data.split(":")[1])
    delete_alert(alert_id, callback.from_user.id)
    await callback.answer("Алерт удалён ✅", show_alert=True)
    await cmd_myalerts(callback.message)


# --- Background price checker ---
async def check_alerts():
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        alerts = get_all_active_alerts()
        if not alerts:
            continue

        coins_needed = list({a[2] for a in alerts})
        prices = get_prices(coins_needed)
        if not prices:
            continue

        triggered: dict[int, list[str]] = {}
        for alert_id, user_id, coin, direction, target in alerts:
            price = prices.get(coin)
            if price is None:
                continue
            hit = (direction == "above" and price >= target) or (direction == "below" and price <= target)
            if hit:
                deactivate_alert(alert_id)
                icon = "📈" if direction == "above" else "📉"
                msg = (f"🔔 *Алерт сработал!*\n\n"
                       f"{icon} *{coin}* достиг ${price:,.2f}\n"
                       f"Ваша цель: ${target:,.2f}")
                triggered.setdefault(user_id, []).append(msg)

        for user_id, msgs in triggered.items():
            for msg in msgs:
                try:
                    await bot.send_message(user_id, msg, parse_mode="Markdown")
                except Exception as e:
                    logging.warning(f"Failed to notify {user_id}: {e}")


async def main():
    logging.info("Crypto alert bot started")
    asyncio.create_task(check_alerts())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

"""
Auto-setup: logs into Telegram as user, messages BotFather,
creates a new bot, saves token to all .env files.

Run: python get_tokens.py
You will need:
  - API ID + API Hash from my.telegram.org (one-time, 1 minute)
  - Your phone number
  - OTP code that arrives in your Telegram app
"""
import asyncio
import os
import re
import sys
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest

# ── Paths to all .env files that need the token ──────────────────────────────
ROOT = Path(__file__).parent.parent
ENV_FILES = [
    ROOT / "ai-telegram-bot" / ".env",
    ROOT / "ai-telegram-bot-pro" / ".env",
    ROOT / "booking-bot" / ".env",
    ROOT / "crypto-alert-bot" / ".env",
]

SESSION_FILE = Path(__file__).parent / "setup_session"


def update_env(path: Path, key: str, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    example = path.parent / ".env.example"
    if not path.exists() and example.exists():
        path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    if path.exists():
        content = path.read_text(encoding="utf-8")
        if f"{key}=" in content:
            content = re.sub(rf"^{key}=.*$", f"{key}={value}", content, flags=re.MULTILINE)
        else:
            content += f"\n{key}={value}\n"
    else:
        content = f"{key}={value}\n"
    path.write_text(content, encoding="utf-8")


async def create_bot(client: TelegramClient, bot_name: str, bot_username: str) -> str | None:
    """Message BotFather and create a new bot. Returns token or None."""
    print("\n[*] Connecting to @BotFather...")
    await client.send_message("BotFather", "/cancel")
    await asyncio.sleep(1)

    await client.send_message("BotFather", "/newbot")
    await asyncio.sleep(2)

    msgs = await client.get_messages("BotFather", limit=1)
    print(f"    BotFather: {msgs[0].text[:80]}")

    await client.send_message("BotFather", bot_name)
    await asyncio.sleep(2)

    msgs = await client.get_messages("BotFather", limit=1)
    print(f"    BotFather: {msgs[0].text[:80]}")

    await client.send_message("BotFather", bot_username)
    await asyncio.sleep(3)

    msgs = await client.get_messages("BotFather", limit=1)
    text = msgs[0].text
    print(f"    BotFather: {text[:120]}")

    token_match = re.search(r"(\d{8,12}:[A-Za-z0-9_-]{35,})", text)
    if token_match:
        return token_match.group(1)

    # Username taken — try with random suffix
    if "username" in text.lower() or "taken" in text.lower() or "invalid" in text.lower():
        import random, string
        suffix = "".join(random.choices(string.digits, k=4))
        new_username = bot_username.rstrip("bot") + suffix + "bot"
        print(f"    Username taken, trying: @{new_username}")
        await client.send_message("BotFather", new_username)
        await asyncio.sleep(3)
        msgs = await client.get_messages("BotFather", limit=1)
        text = msgs[0].text
        token_match = re.search(r"(\d{8,12}:[A-Za-z0-9_-]{35,})", text)
        if token_match:
            return token_match.group(1)

    return None


async def get_my_id(client: TelegramClient) -> int:
    me = await client.get_me()
    return me.id


async def main():
    print("=" * 55)
    print("  Telegram Bot Auto-Setup")
    print("=" * 55)
    print()
    print("Для входа нужны API ID и API Hash.")
    print("Получи их за 1 минуту:")
    print("  1. Открой https://my.telegram.org")
    print("  2. Войди своим номером телефона")
    print("  3. 'API development tools' -> Create application")
    print("  4. Скопируй App api_id и App api_hash")
    print()

    api_id   = input("API ID   : ").strip()
    api_hash = input("API Hash : ").strip()
    phone    = input("Номер телефона (+79...): ").strip()

    print()
    print("[*] Подключаюсь к Telegram...")

    client = TelegramClient(str(SESSION_FILE), int(api_id), api_hash)
    await client.start(phone=phone)

    print("[+] Вход выполнен!")

    me = await client.get_me()
    my_id = me.id
    print(f"[+] Аккаунт: {me.first_name} (id: {my_id})")

    print()
    print("Введи данные нового бота:")
    bot_name     = input("Имя бота (например: My AI Assistant): ").strip() or "My AI Assistant"
    bot_username = input("Username бота без @ (должен кончаться на 'bot'): ").strip()
    if not bot_username.endswith("bot"):
        bot_username += "bot"

    token = await create_bot(client, bot_name, bot_username)

    if not token:
        print("\n[!] Не удалось получить токен автоматически.")
        token = input("    Вставь токен вручную из @BotFather: ").strip()

    print(f"\n[+] Токен получен: {token[:20]}...")

    # Save token to all .env files
    for env_path in ENV_FILES:
        update_env(env_path, "TELEGRAM_TOKEN", token)
        update_env(env_path, "ADMIN_IDS", str(my_id))
        print(f"[+] Записано в {env_path.parent.name}/.env")

    print()
    print("Теперь нужен Anthropic API ключ.")
    print("  1. Открой https://console.anthropic.com")
    print("  2. Settings -> API Keys -> Create Key")
    print("  3. Скопируй ключ (начинается с sk-ant-...)")
    print()
    anthropic_key = input("Anthropic API Key (или Enter чтобы пропустить): ").strip()

    if anthropic_key:
        for env_path in [ROOT / "ai-telegram-bot" / ".env",
                         ROOT / "ai-telegram-bot-pro" / ".env"]:
            update_env(env_path, "ANTHROPIC_API_KEY", anthropic_key)
            print(f"[+] Anthropic key -> {env_path.parent.name}/.env")

    await client.disconnect()

    print()
    print("=" * 55)
    print("  ГОТОВО! Всё настроено.")
    print("=" * 55)
    print()
    print("Запусти бота:")
    print(f"  cd {ROOT / 'ai-telegram-bot-pro'}")
    print("  python bot.py")
    print()
    input("Нажми Enter для выхода...")


if __name__ == "__main__":
    asyncio.run(main())

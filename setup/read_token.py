"""
Takes screenshot of Telegram Desktop, finds BotFather's last message,
copies it via right-click menu, extracts token, saves to .env files.
"""
import re, sys, time
from pathlib import Path
import pyautogui
import pygetwindow as gw
import pyperclip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.2

ROOT = Path(__file__).parent.parent
ENV_FILES = [
    ROOT / "ai-telegram-bot"     / ".env",
    ROOT / "ai-telegram-bot-pro" / ".env",
    ROOT / "booking-bot"         / ".env",
    ROOT / "crypto-alert-bot"    / ".env",
]

TOKEN_RE = re.compile(r"(\d{8,12}:[A-Za-z0-9_\-]{35,})")


def find_win():
    for title in ["Telegram", "Telegram Desktop"]:
        wins = gw.getWindowsWithTitle(title)
        for w in wins:
            if "Telegram" in w.title and "Portfolio" not in w.title:
                return w
    return None


def try_copy_via_rightclick(win):
    """
    Right-click at various positions in the BotFather message area,
    try to click 'Copy Text' from context menu.
    """
    # BotFather messages are on the LEFT side of chat (incoming = left)
    # Chat starts after sidebar (~320px). Messages sit ~40-80px in from sidebar edge.
    chat_left = win.left + 360

    # Try several Y positions (from bottom, above input bar)
    for y_offset in [140, 180, 220, 260, 300, 340]:
        my = win.top + win.height - y_offset

        pyperclip.copy("")          # clear clipboard
        pyautogui.rightClick(chat_left, my)
        time.sleep(0.7)

        # Take small crop to detect context menu
        region = (chat_left, my - 10, 240, 220)
        shot = pyautogui.screenshot(region=region)

        # If a light-background menu appeared (Telegram's light context menu)
        pixel = shot.getpixel((5, 5))
        has_menu = pixel[0] > 180 and pixel[1] > 180 and pixel[2] > 180

        if has_menu:
            print(f"  [+] Контекстное меню появилось (y_offset={y_offset})")
            # "Copy Text" is 2nd item in incoming message menu: ~36px each
            # Typical order for received message: Reply | Copy Text | Pin | ...
            copy_text_y = my + 44   # ~36px per item, "Copy Text" = item 2
            pyautogui.click(chat_left + 60, copy_text_y)
            time.sleep(0.5)

            text = pyperclip.paste()
            if text and TOKEN_RE.search(text):
                return text

            # Maybe it was item 1 (some versions)
            pyautogui.rightClick(chat_left, my)
            time.sleep(0.6)
            pyautogui.click(chat_left + 60, my + 10)
            time.sleep(0.5)
            text = pyperclip.paste()
            if text and TOKEN_RE.search(text):
                return text
        else:
            pyautogui.press("escape")

        time.sleep(0.3)

    return ""


def try_keyboard_copy(win):
    """Press Ctrl+End to scroll to bottom, then try selecting last message."""
    win.activate()
    time.sleep(0.3)
    # Click in chat area (right side, middle height)
    pyautogui.click(win.left + win.width - 200, win.top + win.height // 2)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "end")
    time.sleep(0.5)
    return ""


def update_env(path: Path, key: str, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    example = path.parent / ".env.example"
    if not path.exists() and example.exists():
        path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if f"{key}=" in content:
        content = re.sub(rf"^{key}=.*$", f"{key}={value}", content, flags=re.MULTILINE)
    else:
        content += f"\n{key}={value}\n"
    path.write_text(content, encoding="utf-8")


def save_token(token: str):
    for p in ENV_FILES:
        update_env(p, "TELEGRAM_TOKEN", token)
        print(f"  [+] {p.parent.name}/.env")


def main():
    win = find_win()
    if not win:
        print("[!] Telegram Desktop не найден")
        sys.exit(1)

    win.activate()
    win.maximize()
    time.sleep(0.8)
    print(f"[+] Окно: {win.title}  {win.width}x{win.height}")

    # Scroll to bottom of BotFather chat
    try_keyboard_copy(win)

    print("[*] Ищу токен через правую кнопку мыши...")
    text = try_copy_via_rightclick(win)
    token = TOKEN_RE.search(text)

    if not token:
        # Save a screenshot to show user what we see
        shot_path = str(Path(__file__).parent / "current_tg.png")
        region = (win.left + 300, win.top, win.width - 300, win.height - 60)
        pyautogui.screenshot(shot_path, region=region)
        print(f"[*] Сохранил скриншот: {shot_path}")

        print("\n[!] Не удалось скопировать токен автоматически.")
        print("    Зайди в @BotFather в Telegram Desktop,")
        print("    скопируй токен из последнего сообщения и вставь сюда:")
        raw = input("    Токен: ").strip()
        m = TOKEN_RE.search(raw)
        if not m:
            sys.exit("[!] Токен не распознан")
        token = m

    tok = token.group(1)
    print(f"\n[+] Токен: {tok[:25]}...")
    save_token(tok)
    print("\n[+] ГОТОВО — токен сохранён во всех ботах!")


if __name__ == "__main__":
    main()

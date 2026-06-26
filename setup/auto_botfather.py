"""
Controls Telegram Desktop directly via UI automation.
No credentials needed — Telegram must already be open and logged in.
"""
import os, re, subprocess, sys, time, random, string
from pathlib import Path

import pyautogui
import pygetwindow as gw
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

ROOT = Path(__file__).parent.parent
ENV_FILES = [
    ROOT / "ai-telegram-bot"     / ".env",
    ROOT / "ai-telegram-bot-pro" / ".env",
    ROOT / "booking-bot"         / ".env",
    ROOT / "crypto-alert-bot"    / ".env",
]
BOT_DISPLAY_NAME = "My AI Assistant"
SCREENSHOT_PATH  = str(Path(__file__).parent / "tg_shot.png")


# ── helpers ────────────────────────────────────────────────────────────────────

def find_tg_window():
    for title in ["Telegram", "Telegram Desktop"]:
        wins = gw.getWindowsWithTitle(title)
        if wins:
            return wins[0]
    return None


def launch_telegram():
    username = os.environ.get("USERNAME", "")
    candidates = [
        Path(os.environ.get("APPDATA", ""))      / "Telegram Desktop" / "Telegram.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Telegram Desktop" / "Telegram.exe",
        Path(f"C:/Users/{username}/AppData/Roaming/Telegram Desktop/Telegram.exe"),
    ]
    for p in candidates:
        if p.exists():
            print(f"[*] Запускаю {p.name}...")
            subprocess.Popen([str(p)])
            return True
    return False


def get_window():
    win = find_tg_window()
    if not win:
        print("[*] Telegram не запущен — запускаю...")
        if not launch_telegram():
            sys.exit("[!] Telegram Desktop не найден. Запусти его вручную.")
        for _ in range(15):
            time.sleep(1)
            win = find_tg_window()
            if win:
                break
    if not win:
        sys.exit("[!] Не удалось найти окно Telegram.")
    win.activate()
    win.maximize()
    time.sleep(0.8)
    print(f"[+] Окно найдено: {win.width}x{win.height}")
    return win


def center(win):
    return win.left + win.width // 2, win.top + win.height // 2


def click_center(win):
    pyautogui.click(*center(win))
    time.sleep(0.2)


def send_msg(text: str, delay: float = 2.5):
    """Click input, clear it, type text, press Enter."""
    pyautogui.press("escape")       # close any menu
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    pyautogui.typewrite(text, interval=0.04)
    time.sleep(0.2)
    pyautogui.press("enter")
    print(f"  >> {text}")
    time.sleep(delay)


def open_botfather(win):
    print("[*] Открываю @BotFather...")
    click_center(win)
    pyautogui.hotkey("ctrl", "k")          # Telegram search shortcut
    time.sleep(1.0)
    pyautogui.typewrite("BotFather", interval=0.06)
    time.sleep(1.5)
    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1.2)
    print("[+] @BotFather открыт")


def ocr_window(win) -> str:
    """Screenshot chat area → Windows built-in OCR → return text."""
    # crop: skip sidebar (~320px) and input bar (~65px at bottom)
    region = (win.left + 320, win.top, win.width - 320, win.height - 65)
    pyautogui.screenshot(SCREENSHOT_PATH, region=region)

    abs_path = str(Path(SCREENSHOT_PATH).resolve()).replace("\\", "/")
    ps = f"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime]
$null=[Windows.Storage.StorageFile,Windows.Foundation,ContentType=WindowsRuntime]
function Aw($t){{$a=[System.WindowsRuntimeSystemExtensions]::AsTask($t);$a.Wait();$a.Result}}
$f=Aw([Windows.Storage.StorageFile]::GetFileFromPathAsync("{abs_path}"))
$s=Aw($f.OpenAsync([Windows.Storage.FileAccessMode]::Read))
$d=Aw([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s))
$b=Aw($d.GetSoftwareBitmapAsync())
$e=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$r=Aw($e.RecognizeAsync($b))
$r.Text
"""
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout


def copy_last_message(win) -> str:
    """Right-click last BotFather message → Copy Text → return clipboard."""
    # BotFather messages appear on the LEFT side of the chat area
    # Chat area starts at win.left+320; message bubble is ~40px in from there
    # Last message is just above the input bar (~65px from bottom)
    for y_delta in [130, 160, 200, 240]:
        mx = win.left + 370           # left side of chat = incoming messages
        my = win.top + win.height - y_delta
        pyautogui.rightClick(mx, my)
        time.sleep(0.6)

        # Take small screenshot to see if a context menu appeared
        shot = pyautogui.screenshot(region=(mx - 5, my - 5, 250, 200))
        # Look for context menu: it's a light rectangle appearing near cursor
        # Heuristic: if pixels right of click are lighter than before, menu appeared
        px = shot.getpixel((10, 10))
        is_menu = px[0] > 200 and px[1] > 200 and px[2] > 200  # light background

        if is_menu:
            # "Copy Text" is typically the 2nd item (~36px each, first at +18)
            # Order: Reply(0), Copy Text(1) for received messages
            pyautogui.click(mx + 80, my + 54)
            time.sleep(0.4)
            text = pyperclip.paste()
            if text and len(text) > 20:
                return text
        else:
            pyautogui.press("escape")
            time.sleep(0.3)
    return ""


def extract_token(text: str):
    m = re.search(r"(\d{8,12}:[A-Za-z0-9_\-]{35,})", text)
    return m.group(1) if m else None


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


def save_to_all(key: str, value: str):
    for p in ENV_FILES:
        update_env(p, key, value)
        print(f"  [+] {p.parent.name}/.env  {key}=***")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 52)
    print("  Telegram Bot Auto-Creator (UI Automation)")
    print("=" * 52)
    print()

    win = get_window()
    open_botfather(win)

    suffix   = "".join(random.choices(string.digits, k=5))
    username = f"aihelper{suffix}bot"

    print(f"[*] Создаю бота @{username}...")
    send_msg("/cancel", delay=1.5)
    send_msg("/newbot", delay=3.0)
    send_msg(BOT_DISPLAY_NAME, delay=3.0)
    send_msg(username, delay=4.0)        # wait longer for BotFather's token reply

    token = None

    # Strategy 1: Windows OCR on screenshot
    print("[*] Читаю токен через OCR...")
    ocr_text = ocr_window(win)
    token = extract_token(ocr_text)
    if token:
        print(f"[+] Токен найден через OCR: {token[:20]}...")

    # Strategy 2: right-click → Copy Text → clipboard
    if not token:
        print("[*] OCR не помог, пробую Copy Text через правую кнопку...")
        clipboard_text = copy_last_message(win)
        token = extract_token(clipboard_text)
        if token:
            print(f"[+] Токен найден через буфер: {token[:20]}...")

    # Strategy 3: re-screenshot after slight scroll and retry OCR
    if not token:
        print("[*] Прокручиваю чат вниз и пробую ещё раз...")
        click_center(win)
        pyautogui.hotkey("ctrl", "end")
        time.sleep(1)
        ocr_text = ocr_window(win)
        token = extract_token(ocr_text)

    if not token:
        print()
        print("[!] Автоматически токен не удалось прочитать.")
        print("    Скопируй токен из @BotFather (он уже там) и вставь:")
        token = input("    Токен: ").strip()
        token = extract_token(token) or token

    if not token:
        sys.exit("[!] Токен не получен.")

    print()
    print(f"[+] Токен: {token[:25]}...")
    print("[*] Сохраняю в .env файлы...")
    save_to_all("TELEGRAM_TOKEN", token)

    # Also save admin ID — get my Telegram ID from saved messages trick
    # We can't get user ID easily without API, skip for now
    # User can add ADMIN_IDS manually later

    print()
    print("=" * 52)
    print(f"  ГОТОВО! Бот @{username} создан.")
    print("=" * 52)
    print()
    print("Следующий шаг:")
    print("  1. Добавь ADMIN_IDS=<твой_id> в .env файлы")
    print("     (свой ID узнай у @userinfobot)")
    print("  2. Добавь ANTHROPIC_API_KEY в ai-telegram-bot-pro/.env")
    print("  3. Запусти: cd projects/ai-telegram-bot-pro && python bot.py")
    print()
    input("Нажми Enter для выхода...")


if __name__ == "__main__":
    main()

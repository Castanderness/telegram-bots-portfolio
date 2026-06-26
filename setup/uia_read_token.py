"""
Uses Windows UI Automation (pywinauto) to read text directly from
Telegram Desktop's accessibility tree — no OCR, no screenshots.
"""
import re, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOKEN_RE = re.compile(r"(\d{8,12}:[A-Za-z0-9_\-]{35,})")
ENV_FILES = [
    ROOT / "ai-telegram-bot"     / ".env",
    ROOT / "ai-telegram-bot-pro" / ".env",
    ROOT / "booking-bot"         / ".env",
    ROOT / "crypto-alert-bot"    / ".env",
]

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
    from pywinauto import Application, Desktop
    from pywinauto.keyboard import send_keys
    import pyperclip

    print("[*] Ищу окно Telegram Desktop...")
    desktop = Desktop(backend="uia")

    tg_win = None
    for win in desktop.windows():
        try:
            title = win.window_text()
            if "Telegram" in title and "Portfolio" not in title and "Claude" not in title:
                tg_win = win
                print(f"[+] Найдено: '{title}'")
                break
        except Exception:
            continue

    if not tg_win:
        print("[!] Telegram Desktop не найден. Запусти его.")
        sys.exit(1)

    tg_win.set_focus()
    time.sleep(0.8)

    # Try to get all text from the window via accessibility tree
    print("[*] Читаю accessibility tree...")
    all_text = []
    try:
        texts = tg_win.descendants(control_type="Text")
        for t in texts:
            try:
                val = t.window_text()
                if val.strip():
                    all_text.append(val)
            except Exception:
                pass
    except Exception as e:
        print(f"  text descendants: {e}")

    # Also try Edit controls (message input area etc)
    try:
        edits = tg_win.descendants(control_type="Edit")
        for e_ctrl in edits:
            try:
                val = e_ctrl.get_value()
                if val:
                    all_text.append(val)
            except Exception:
                pass
    except Exception as e:
        print(f"  edit descendants: {e}")

    full_text = "\n".join(all_text)
    print(f"[*] Extracted {len(all_text)} text elements, {len(full_text)} chars")

    token_match = TOKEN_RE.search(full_text)
    if token_match:
        token = token_match.group(1)
        print(f"[+] Токен найден: {token[:25]}...")
        save_token(token)
        print("\n[+] ГОТОВО! Токен сохранён во всех ботах.")
        return

    # Token not found in accessibility tree — navigate to BotFather via keyboard
    print("[*] Токен не найден в дереве, перехожу к @BotFather...")
    tg_win.set_focus()
    time.sleep(0.5)

    # Open search
    send_keys("^k")
    time.sleep(0.8)
    send_keys("BotFather", with_spaces=False)
    time.sleep(1.5)
    send_keys("{DOWN}{ENTER}")
    time.sleep(1.5)

    # Re-scan accessibility tree
    all_text = []
    try:
        texts = tg_win.descendants(control_type="Text")
        for t in texts:
            try:
                val = t.window_text()
                if val.strip():
                    all_text.append(val)
            except Exception:
                pass
    except Exception:
        pass

    full_text = "\n".join(all_text)
    print(f"[*] После навигации: {len(full_text)} chars")

    if len(full_text) > 50:
        # Print last 2000 chars to help debug
        preview = full_text[-2000:]
        print("--- TEXT PREVIEW (last 2000 chars) ---")
        print(preview)
        print("--- END ---")

    token_match = TOKEN_RE.search(full_text)
    if token_match:
        token = token_match.group(1)
        print(f"\n[+] Токен: {token[:25]}...")
        save_token(token)
        print("\n[+] ГОТОВО!")
    else:
        print("\n[!] Токен не найден через UI Automation.")
        print("    Telegram Desktop, возможно, не отдаёт текст через accessibility API.")
        print()
        print("    ЕДИНСТВЕННЫЙ оставшийся вариант:")
        print("    Открой @BotFather → скопируй токен → вставь:")
        raw = input("    > ").strip()
        m = TOKEN_RE.search(raw)
        if m:
            save_token(m.group(1))
            print("[+] ГОТОВО!")
        else:
            print("[!] Токен не распознан.")

if __name__ == "__main__":
    main()

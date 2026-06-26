"""
Connects to Yandex Browser via CDP, tries Google OAuth auto-login on Anthropic console,
creates API key, saves to .env files.
"""
import asyncio, re, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent.parent
ENV_FILES = [
    ROOT / "ai-telegram-bot"     / ".env",
    ROOT / "ai-telegram-bot-pro" / ".env",
]


def update_env(path: Path, key: str, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if f"{key}=" in content:
        content = re.sub(rf"^{key}=.*$", f"{key}={value}", content, flags=re.MULTILINE)
    else:
        content += f"\n{key}={value}\n"
    path.write_text(content, encoding="utf-8")


async def try_get_key(page) -> str | None:
    """Try to extract API key from the keys page."""
    await asyncio.sleep(2)
    content = await page.content()

    # Look for key pattern in page source
    m = re.search(r"(sk-ant-api\d*-[A-Za-z0-9_\-]{20,})", content)
    if m:
        return m.group(1)

    # Try visible elements
    for sel in ["input[value^='sk-ant']", "code:has-text('sk-ant')", "span:has-text('sk-ant')"]:
        try:
            els = page.locator(sel)
            count = await els.count()
            for i in range(count):
                el = els.nth(i)
                if await el.is_visible(timeout=500):
                    try:
                        val = await el.input_value()
                    except Exception:
                        val = await el.inner_text()
                    if val and "sk-ant" in val:
                        return val.strip()
        except Exception:
            pass
    return None


async def create_key(page) -> str | None:
    """Click Create Key, fill name, confirm, return key."""
    for btn_sel in [
        "button:has-text('Create Key')",
        "button:has-text('New Key')",
        "button:has-text('+ Create')",
        "button:has-text('Add Key')",
    ]:
        try:
            btn = page.locator(btn_sel).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                print(f"[+] Clicked: {btn_sel}")
                await asyncio.sleep(1.5)
                break
        except Exception:
            pass

    # Fill name
    for inp_sel in ["input[placeholder*='ame']", "input[placeholder*='key']", "input[type='text']"]:
        try:
            inp = page.locator(inp_sel).first
            if await inp.is_visible(timeout=1500):
                await inp.fill("FreelanceBot")
                await asyncio.sleep(0.5)
                break
        except Exception:
            pass

    # Confirm
    for conf_sel in ["button:has-text('Create Key')", "button:has-text('Create')", "button[type='submit']"]:
        try:
            btn = page.locator(conf_sel).last
            if await btn.is_visible(timeout=1500):
                await btn.click()
                print(f"[+] Confirmed: {conf_sel}")
                await asyncio.sleep(2.5)
                break
        except Exception:
            pass

    return await try_get_key(page)


async def main():
    async with async_playwright() as pw:
        print("[*] Connecting to Yandex Browser via CDP...")
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]

        # Get or open Anthropic keys page
        page = None
        for pg in context.pages:
            if "anthropic" in pg.url or "claude.com" in pg.url:
                page = pg
                break
        if not page:
            page = await context.new_page()

        print("[*] Navigating to Anthropic console...")
        await page.goto("https://console.anthropic.com/settings/keys",
                        wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        print(f"[*] URL: {page.url}")

        # If not logged in — try Google OAuth
        if "login" in page.url or "sign" in page.url:
            print("[*] Not logged in — trying Google OAuth...")
            for btn_sel in [
                "button:has-text('Google')",
                "a:has-text('Google')",
                "[data-provider='google']",
                "button:has-text('Continue with Google')",
            ]:
                try:
                    btn = page.locator(btn_sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        print(f"[+] Clicked Google login: {btn_sel}")
                        await asyncio.sleep(4)
                        break
                except Exception:
                    pass

            print(f"[*] After Google click URL: {page.url}")

            # If Google account chooser appeared, pick first account
            if "accounts.google.com" in page.url:
                print("[*] Google account chooser — selecting first account...")
                try:
                    acc = page.locator("[data-email], li[data-identifier]").first
                    if await acc.is_visible(timeout=3000):
                        await acc.click()
                        await asyncio.sleep(3)
                except Exception:
                    pass

            # Wait for redirect back to Anthropic
            await asyncio.sleep(3)
            print(f"[*] Final URL: {page.url}")

        # If still on login page, take screenshot to see state
        if "login" in page.url or "sign" in page.url:
            await page.screenshot(path=str(Path(__file__).parent / "login_state.png"))
            print("[!] Still on login page — screenshot: setup/login_state.png")
            await browser.close()
            return

        # Navigate to keys page if needed
        if "keys" not in page.url:
            await page.goto("https://console.anthropic.com/settings/keys",
                            wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)

        print(f"[*] Keys page: {page.url}")

        # Try to create key
        api_key = await create_key(page)

        if not api_key:
            await page.screenshot(path=str(Path(__file__).parent / "keys_page.png"))
            print("[!] Could not extract key — screenshot: setup/keys_page.png")
            await browser.close()
            return

        print(f"\n[+] API Key: {api_key[:20]}...")
        for p_file in ENV_FILES:
            update_env(p_file, "ANTHROPIC_API_KEY", api_key)
            print(f"[+] Saved: {p_file.parent.name}/.env")

        print("\n[+] DONE!")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

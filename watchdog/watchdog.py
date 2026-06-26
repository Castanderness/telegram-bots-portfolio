"""
Watchdog: monitors bot process, restarts if crashed.
Logs restarts to watchdog.log.
"""
import subprocess, sys, time, logging
from datetime import datetime
from pathlib import Path

BOT_DIR  = Path(__file__).parent.parent / "ai-telegram-bot-pro"
BOT_CMD  = [sys.executable, "bot.py"]
LOG_FILE = Path(__file__).parent / "watchdog.log"
CHECK_INTERVAL = 10   # seconds between health checks
MAX_RESTARTS   = 20   # per hour before giving up

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)

def run():
    restarts = 0
    hour_start = time.time()

    logging.info("Watchdog started")
    proc = subprocess.Popen(BOT_CMD, cwd=BOT_DIR)
    logging.info(f"Bot started PID={proc.pid}")

    while True:
        time.sleep(CHECK_INTERVAL)

        # Reset restart counter every hour
        if time.time() - hour_start > 3600:
            restarts = 0
            hour_start = time.time()

        if proc.poll() is not None:
            exit_code = proc.returncode
            logging.warning(f"Bot died (exit={exit_code}), restarting... [{restarts+1}/{MAX_RESTARTS}]")

            if restarts >= MAX_RESTARTS:
                logging.error("Too many restarts. Stopping watchdog.")
                break

            time.sleep(3)
            proc = subprocess.Popen(BOT_CMD, cwd=BOT_DIR)
            restarts += 1
            logging.info(f"Bot restarted PID={proc.pid}")

if __name__ == "__main__":
    run()

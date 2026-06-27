"""
Monitor job boards for Telegram bot projects.
Sends alert to bot @ai_asst_955338_bot when new relevant project appears.
Runs as background daemon.
"""
import requests, time, json, re, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

BOT_TOKEN   = "8657127251:AAHkpVH15EBu2VWID62bG1OMDFE33BJLsuk"
ADMIN_ID    = 21441
SEEN_FILE   = Path(__file__).parent / "seen_jobs.json"
CHECK_EVERY = 1800  # 30 minutes

KEYWORDS = ["telegram bot", "telegram бот", "чат бот", "chatbot", "python bot",
            "автоматизация telegram", "разработка бота", "telegram developer"]


def load_seen() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(ids: set):
    SEEN_FILE.write_text(json.dumps(list(ids)))


def send_alert(text: str):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": ADMIN_ID, "text": text, "parse_mode": "Markdown"},
        timeout=10
    )


def check_hh_ru() -> list[dict]:
    """Check HH.ru for new freelance bot projects."""
    results = []
    for kw in KEYWORDS[:3]:
        try:
            r = requests.get(
                "https://api.hh.ru/vacancies",
                params={"text": kw, "schedule": "remote", "per_page": 10,
                        "order_by": "publication_time", "area": 113},
                headers={"User-Agent": "JobMonitor/1.0"},
                timeout=10
            )
            for v in r.json().get("items", []):
                salary = v.get("salary") or {}
                sal_str = ""
                if salary.get("from"):
                    sal_str = f" — от {salary['from']:,} {salary.get('currency','RUB')}"
                results.append({
                    "id": f"hh_{v['id']}",
                    "title": v["name"],
                    "company": v.get("employer", {}).get("name", "—"),
                    "salary": sal_str,
                    "url": v["alternate_url"],
                    "source": "HH.ru"
                })
        except Exception as e:
            logging.warning(f"HH error: {e}")
    return results


def check_fl_ru_jobs() -> list[dict]:
    """Check FL.ru for new bot projects via their API."""
    results = []
    try:
        r = requests.get(
            "https://api.fl.ru/v1/projects",
            params={"q": "telegram бот", "count": 10, "kind": "5"},
            headers={"User-Agent": "JobMonitor/1.0"},
            timeout=10
        )
        if r.status_code == 200:
            for p in r.json().get("list", []):
                results.append({
                    "id": f"fl_{p.get('id')}",
                    "title": p.get("name", "—"),
                    "budget": p.get("budget", "—"),
                    "url": f"https://www.fl.ru/projects/{p.get('id')}/",
                    "source": "FL.ru"
                })
    except Exception as e:
        logging.warning(f"FL.ru error: {e}")
    return results


def check_kwork_api() -> list[dict]:
    """Check Kwork for new bot orders."""
    results = []
    try:
        r = requests.get(
            "https://api.kwork.ru/wants",
            params={"search": "telegram бот", "count": 10},
            headers={"User-Agent": "JobMonitor/1.0"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            for item in data.get("response", []):
                results.append({
                    "id": f"kwork_{item.get('id')}",
                    "title": item.get("name", "—"),
                    "budget": f"{item.get('priceLimit', '?')} ₽",
                    "url": f"https://kwork.ru/wants/{item.get('id')}/",
                    "source": "Kwork"
                })
    except Exception as e:
        logging.warning(f"Kwork error: {e}")
    return results


def run_once():
    seen = load_seen()
    all_jobs = []
    all_jobs.extend(check_hh_ru())
    all_jobs.extend(check_fl_ru_jobs())
    all_jobs.extend(check_kwork_api())

    new_jobs = [j for j in all_jobs if j["id"] not in seen]
    logging.info(f"Found {len(all_jobs)} jobs, {len(new_jobs)} new")

    for job in new_jobs:
        msg = (f"🔔 *Новый заказ: {job['source']}*\n\n"
               f"📋 {job['title']}\n"
               f"💰 {job.get('salary') or job.get('budget', '—')}\n"
               f"🔗 {job['url']}")
        try:
            send_alert(msg)
            logging.info(f"Alerted: {job['title'][:50]}")
        except Exception as e:
            logging.error(f"Alert error: {e}")
        seen.add(job["id"])

    save_seen(seen)
    return len(new_jobs)


if __name__ == "__main__":
    logging.info("Job monitor started — checking every 30 min")
    logging.info(f"Keywords: {KEYWORDS[:3]}")

    # Run first check immediately
    found = run_once()
    logging.info(f"First check: {found} new jobs")

    while True:
        time.sleep(CHECK_EVERY)
        found = run_once()
        logging.info(f"Check done: {found} new jobs")

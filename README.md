# Telegram Bot Developer — Python Portfolio

> **Open for freelance projects** | 2-5 day delivery | Starting from $49

---

## Available Services

| Service | Price | Delivery |
|---------|-------|----------|
| AI Telegram Bot (Claude/ChatGPT) | from $49 | 3-5 days |
| Appointment Booking Bot | from $79 | 3-5 days |
| Crypto Price Alert Bot | from $59 | 2-3 days |
| Restaurant Bot (menu + reservations) | from $99 | 4-7 days |
| Web Scraper → CSV/Excel | from $35 | 1-3 days |
| Excel Automation Scripts | from $29 | 1-2 days |
| Job Vacancy Telegram Channel | from $69 | 2-4 days |
| Survey Bot → Excel Export | from $59 | 2-4 days |

---

## Bots in This Repository

### 1. `ai-telegram-bot-pro/` — AI Assistant with Subscription
- Free tier: 20 messages/day
- Premium: unlimited
- Admin panel with stats
- SQLite persistent storage

### 2. `booking-bot/` — Appointment Scheduling Bot
- Interactive date/time picker
- No double-booking logic
- Instant admin notifications
- SQLite database

### 3. `crypto-alert-bot/` — Price Alert Bot
- Set price targets for BTC/ETH/SOL/TON
- Live data from CoinGecko (free API)
- Checks every 60 seconds

### 4. `vacancy-bot/` — Job Vacancy Channel
- Pulls from HH.ru API every 2 hours
- Posts new vacancies automatically
- Tracks posted IDs (no duplicates)

### 5. `auto-content-bot/` — Auto-Posting Channel
- Daily crypto price updates
- Educational tips on schedule
- APScheduler integration

### 6. `restaurant-bot/` — Restaurant Bot
- Browse menu by category
- Book a table (date/time picker)
- Admin notification for each reservation

### 7. `tutor-bot/` — English Tutor Bot
- Word of the day
- Vocabulary quizzes
- Grammar tips
- No AI API needed

### 8. `survey-bot/` — Survey → Excel
- Multi-step surveys (ratings, choices, text)
- Auto-exports to `.xlsx`
- Admin receives results instantly

### 9. `price-monitor-bot/` — Avito Price Monitor
- Tracks listings by search query
- Alerts on new items and price drops

---

## Tech Stack
- **Python 3.12** + **aiogram 3.7** (FSM, inline keyboards)
- **SQLite** for persistence (zero setup)
- **Anthropic Claude Haiku** (~$0.001/1000 messages)
- **CoinGecko API** (free, no key required)
- **HH.ru API** (free)
- **APScheduler** for cron jobs
- **openpyxl** for Excel export

---

## Setup (any bot)
```bash
git clone https://github.com/Castanderness/telegram-bots-portfolio
cd ai-telegram-bot-pro
pip install -r requirements.txt
cp .env.example .env
# Fill TELEGRAM_TOKEN and ANTHROPIC_API_KEY in .env
python bot.py
```

---

## Contact / Hire Me

**Portfolio site:** https://castanderness.github.io/telegram-bots-portfolio/portfolio/

**Dev.to article:** https://dev.to/castanderness/i-built-9-production-ready-telegram-bots-in-python-open-source-345h

Available for freelance projects on Fiverr, Freelancer, and direct contact.

*2-5 day delivery | Clean Python code | 7-day support included*

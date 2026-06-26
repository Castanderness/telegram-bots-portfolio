# Telegram Bot Developer — Production-Ready Python Bots

**9 ready-to-deploy Telegram bots** built for freelance sales and subscription income.

[![Portfolio](https://img.shields.io/badge/Portfolio-Live-brightgreen)](https://castanderness.github.io/telegram-bots-portfolio/portfolio/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.7-orange)](https://docs.aiogram.dev)

---

## Available Bots

| Bot | Features | Sell Price |
|-----|----------|-----------|
| **AI Assistant Pro** | Claude/GPT, subscription tiers, admin panel, SQLite | $99–199 |
| **Booking Bot** | Date/time picker, no double-booking, admin notifications | $79–249 |
| **Crypto Alert Bot** | Live CoinGecko prices, custom alerts, 10+ coins | $59–199 |
| **Vacancy Channel Bot** | HH.ru API, auto-posts new jobs, duplicate filter | $69–149 |
| **Auto-Content Bot** | Daily crypto news + tips, scheduled posts | $50–100 |
| **Price Monitor Bot** | Avito scraper, price drop alerts | $80–150 |
| **Tutor Bot** | English words/phrases/grammar, quizzes | $80–150 |
| **Restaurant Bot** | Menu, table booking, admin order view | $150–300 |
| **Survey Bot** | Custom questions, saves answers to Excel | $60–120 |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/Castanderness/telegram-bots-portfolio.git
cd telegram-bots-portfolio

# Install all dependencies
pip install aiogram==3.7.0 anthropic python-dotenv requests beautifulsoup4 openpyxl apscheduler fastapi uvicorn

# Setup AI assistant bot
cd ai-telegram-bot-pro
cp .env.example .env
# Fill TELEGRAM_TOKEN + ANTHROPIC_API_KEY in .env
python bot.py
```

---

## Tech Stack

- **Python 3.12** — clean, typed code
- **aiogram 3.x** — modern async Telegram framework  
- **Anthropic Claude API** — AI responses (Haiku model, very cheap)
- **SQLite** — persistent storage, no external DB needed
- **APScheduler** — scheduled tasks for auto-posting bots
- **BeautifulSoup4** — web scraping
- **openpyxl** — Excel reports with charts

---

## Services

All bots are available as **custom development services**:

- Customize system prompt, branding, language
- Add payment integration (Telegram Stars, USDT)
- Deploy to VPS (included in Premium packages)

**Contact:** Available on Fiverr, Kwork, Freelancer.com

**Portfolio:** [castanderness.github.io/telegram-bots-portfolio](https://castanderness.github.io/telegram-bots-portfolio/portfolio/)

---

## Project Structure

```
projects/
├── ai-telegram-bot/          # Basic AI assistant
├── ai-telegram-bot-pro/      # AI + subscriptions + admin
├── booking-bot/              # Appointment scheduler
├── crypto-alert-bot/         # Price alerts
├── auto-content-bot/         # Channel automation
├── vacancy-bot/              # Job board aggregator
├── price-monitor-bot/        # Avito price tracker
├── tutor-bot/                # English tutor
├── restaurant-bot/           # Restaurant assistant
├── survey-bot/               # Feedback collector
├── chat-widget/              # Website chatbot (FastAPI)
├── web-parser/               # Universal web scraper
├── automation-scripts/       # Excel automation
├── portfolio/                # HTML portfolio site
└── fiverr-gigs/              # Gig descriptions (EN)
```

# Roadmap: Заработок с Claude из России
*Обновлено: 2026-06-26*

---

## Что готово (100%)

### Инфраструктура
- [x] Python 3.12.10 установлен
- [x] Все пакеты установлены (aiogram, anthropic, requests, bs4, openpyxl)
- [x] NO_PROXY настроен под твой SOCKS прокси

### Продукты для продажи

| Продукт | Папка | Цена | Статус |
|---|---|---|---|
| AI-бот (базовый) | `ai-telegram-bot/` | $49–99 | ✅ Работает |
| AI-бот PRO + подписка + БД | `ai-telegram-bot-pro/` | $99–199 | ✅ Работает |
| Бот записи клиентов | `booking-bot/` | $79–249 | ✅ Работает |
| Крипто-алерты (live API) | `crypto-alert-bot/` | $59–199 | ✅ Работает |
| Веб-парсер (60 книг спарсено) | `web-parser/` | $35–150 | ✅ + демо-данные |
| Excel автоматизация | `automation-scripts/` | $29–149 | ✅ + реальный .xlsx |

### Маркетинг
- [x] 5 гигов для Fiverr (`fiverr-gigs/`)
- [x] Портфолио-сайт (`portfolio/index.html`) — тёмная тема, 6 карточек услуг
- [x] 3 шаблона предложений Freelancer.com (`proposal-templates/`)
- [x] Скрипт деплоя на VPS (`deploy/setup_vps.sh`)

---

## Что делать тебе (требует твоих аккаунтов)

### Шаг 1 — Запусти AI-бот PRO (сегодня, 10 мин)
```
cd c:\Claude\projects\ai-telegram-bot-pro
copy .env.example .env
```
Открой .env, заполни:
- TELEGRAM_TOKEN — от @BotFather
- ANTHROPIC_API_KEY — от console.anthropic.com
- ADMIN_IDS — твой Telegram ID (узнать у @userinfobot)

Запуск: `start.bat`

### Шаг 2 — Опубликуй гиги на Fiverr (сегодня, 30 мин)
Открой каждый файл и скопируй в Fiverr:
1. `fiverr-gigs/gig1_telegram_bot.md`
2. `fiverr-gigs/gig2_web_scraper.md`
3. `fiverr-gigs/gig3_automation.md`
4. `fiverr-gigs/gig4_booking_bot.md`
5. `fiverr-gigs/gig5_crypto_bot.md`

### Шаг 3 — Портфолио (уже готово, открой)
`portfolio/index.html` — открой в браузере, проверь.
Можно залить бесплатно на GitHub Pages.

### Шаг 4 — Freelancer.com (параллельно)
- Зарегистрируйся
- В разделе "Browse Projects" ищи: `telegram bot`, `python scraper`, `automation`
- Отвечай шаблонами из `proposal-templates/`

---

## Целевой доход

| Период | Цель | Как |
|---|---|---|
| Неделя 1–2 | $100–200 | Первые заказы по сниженной цене (ради отзывов) |
| Месяц 1 | $300–500 | Fiverr + Freelancer, 3–8 заказов |
| Месяц 2 | $600–1000 | Повторные клиенты + свой SaaS бот |
| Месяц 3+ | $1000–2500 | Нишевые боты на подписке + заказы |

## Пассивный доход (запусти сам-бот с подпиской)
- AI-бот PRO как публичный сервис
- Бесплатно: 20 сообщений/день
- Premium: $15/мес (USDT или Telegram Stars)
- **10 платящих = $150/мес пассивно**
- **50 платящих = $750/мес пассивно**

---

## Вывод денег
| Способ | Комиссия | Скорость |
|---|---|---|
| Payoneer → Bestchange.ru | ~2–3% | 1–3 дня |
| USDT TRC-20 → Bybit P2P | ~0.5–1% | Моментально |
| Wise (если есть не-РФ счёт) | 0.5% | 1–2 дня |

# AI Telegram Bot — Setup Guide

## Быстрый старт (5 минут)

### 1. Установи зависимости
```bash
pip install -r requirements.txt
```

### 2. Создай .env файл
```bash
copy .env.example .env
```
Открой `.env` и заполни:
- `TELEGRAM_TOKEN` — получи у [@BotFather](https://t.me/BotFather) командой `/newbot`
- `ANTHROPIC_API_KEY` — получи на [console.anthropic.com](https://console.anthropic.com)

### 3. Запусти
```bash
python bot.py
```

## Настройка под клиента

Измени `SYSTEM_PROMPT` в `.env`:
```
# Для магазина:
SYSTEM_PROMPT=You are a helpful assistant for TechStore. Help customers with product questions. Be friendly and concise.

# Для юриста:
SYSTEM_PROMPT=You are a legal assistant. Help users understand basic legal concepts. Always recommend consulting a real lawyer for specific cases.
```

## Деплой на сервер (чтобы работало 24/7)

### Вариант 1: Railway.app (бесплатно/дёшево)
1. Зарегистрируйся на railway.app
2. Создай новый проект → "Deploy from GitHub"
3. Добавь переменные окружения в Railway Settings
4. Деплой автоматический

### Вариант 2: VPS (Hostinger/Hetzner ~$4/мес)
```bash
# На сервере:
git clone <repo>
pip install -r requirements.txt
cp .env.example .env
nano .env  # заполни токены

# Запуск как сервис (чтобы не падал):
nohup python bot.py &
# или через systemd/screen
```

## Стоимость API (примерная)
- Claude Haiku: ~$0.001 за 1000 сообщений (очень дёшево)
- Claude Sonnet: ~$0.01 за 1000 сообщений
- Для небольшого бота (100-500 сообщений/день) = $1-5/мес

## Что можно добавить (для более дорогих заказов)
- [ ] Оплата через Stars (Telegram payments)
- [ ] Подписочная модель
- [ ] Статистика пользователей
- [ ] Inline-кнопки / меню
- [ ] Загрузка файлов и обработка изображений
- [ ] Интеграция с CRM

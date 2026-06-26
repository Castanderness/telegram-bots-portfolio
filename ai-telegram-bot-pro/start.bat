@echo off
set NO_PROXY=*
set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%

if not exist .env (
    echo ERROR: .env not found. Copy .env.example to .env and fill tokens.
    pause & exit /b 1
)

echo Starting AI Telegram Bot PRO...
python bot.py
pause

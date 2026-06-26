@echo off
set NO_PROXY=*
set PYTHONPATH=%~dp0
set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%

if not exist .env (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and fill in your tokens.
    pause
    exit /b 1
)

echo Starting AI Telegram Bot...
python bot.py
pause

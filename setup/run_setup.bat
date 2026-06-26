@echo off
set NO_PROXY=*
set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%
title Telegram Bot Auto-Creator
echo Убедись что Telegram Desktop открыт и залогинен.
echo Скрипт сам нажмет все кнопки.
echo.
python auto_botfather.py
pause

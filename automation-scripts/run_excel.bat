@echo off
set NO_PROXY=*
set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%
echo Running Excel Report Generator...
python excel_automation.py
echo Done! Check sales_report.xlsx
pause

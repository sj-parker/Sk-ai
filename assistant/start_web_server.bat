@echo off
echo Запуск веб-сервера...
cd /d "%~dp0"
cd web_overlay
python web_server.py
pause 
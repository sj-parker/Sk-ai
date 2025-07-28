@echo off
chcp 65001 >nul
title Ассистент - Только Python

start "Ассистент" cmd /k "cd assistant && call venv\Scripts\activate.bat && py main.py"

timeout /t 3 /nobreak >nul
start http://localhost:31994
timeout /t 1 /nobreak >nul
start http://localhost:31991

echo.
echo ========================================
echo    ✅ Ассистент запущен!
echo ========================================
pause 
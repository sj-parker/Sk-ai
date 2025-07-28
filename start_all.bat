@echo off
chcp 65001 >nul
title VRM + Ассистент - Быстрый запуск

:: Запуск ассистента
start "Ассистент" cmd /k "cd assistant && call venv\Scripts\activate.bat && py main.py"

:: Запуск VRM
start "VRM" cmd /k "cd VRMoverlay && npm run dev"

:: Открытие браузеров
timeout /t 5 /nobreak >nul
start http://localhost:3001
timeout /t 1 /nobreak >nul
start http://localhost:31994
timeout /t 1 /nobreak >nul
start http://localhost:31991

echo.
echo ========================================
echo    ✅ Всё запущено!
echo ========================================
pause 
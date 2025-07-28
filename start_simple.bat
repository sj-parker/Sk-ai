@echo off
chcp 65001 >nul
title VRM + Ассистент - Быстрый запуск

echo.
echo ========================================
echo    🚀 VRM + Ассистент - Быстрый запуск
echo ========================================
echo.

:: Быстрая проверка Python
echo 🔍 Проверка Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python найден

:: Пропускаем проверку Node.js/npm для ускорения
echo ⚡ Пропускаем проверку Node.js/npm для быстрого запуска
echo 💡 Убедитесь, что Node.js установлен

:: Проверяем папки
if not exist "assistant" (
    echo ❌ Папка 'assistant' не найдена!
    pause
    exit /b 1
)
if not exist "VRMoverlay" (
    echo ❌ Папка 'VRMoverlay' не найдена!
    pause
    exit /b 1
)

:: Быстрая установка Python зависимостей
echo 📦 Установка Python зависимостей...
cd assistant
if not exist "venv" (
    echo Создание виртуального окружения...
    py -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
cd ..

:: Запуск ассистента
echo 🤖 Запуск ассистента...
start "Ассистент" cmd /k "cd assistant && call venv\Scripts\activate.bat && py main.py"

timeout /t 3 /nobreak >nul

:: Попытка запустить VRM
echo 🎭 Попытка запуска VRM...
start "VRM" cmd /k "cd VRMoverlay && npm run dev"

timeout /t 5 /nobreak >nul

echo 🌐 Открытие браузеров...
start http://localhost:3001
timeout /t 1 /nobreak >nul
start http://localhost:31994
timeout /t 1 /nobreak >nul
start http://localhost:31991

echo.
echo ========================================
echo    ✅ Система запущена!
echo ========================================
echo.
echo 📱 VRM приложение: http://localhost:3001
echo 📊 Мониторинг ассистента: http://localhost:31994
echo 🖼️ Overlay: http://localhost:31991
echo.
echo 💡 Если VRM не запустился, проверьте Node.js
echo 💡 Для остановки закройте окна терминалов
echo.
pause 
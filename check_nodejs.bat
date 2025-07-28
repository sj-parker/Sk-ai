@echo off
chcp 65001 >nul
title Проверка Node.js

echo.
echo ========================================
echo    🔍 Проверка Node.js
echo ========================================
echo.

:: Проверяем Node.js
echo 🔍 Проверка Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js не найден!
    echo.
    echo 📥 Установите Node.js:
    echo 💻 https://nodejs.org/
    echo.
    echo 💡 Выберите LTS версию
    echo 💡 При установке отметьте "Add to PATH"
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set "node_version=%%i"
    echo ✅ Node.js найден: %node_version%
)

:: Пытаемся проверить npm (но не зависаем)
echo.
echo 🔍 Проверка npm...
echo ⏳ Проверка может занять несколько секунд...
timeout /t 3 /nobreak >nul

:: Используем PowerShell для проверки с таймаутом
powershell -Command "try { $null = npm --version; Write-Host '✅ npm найден' } catch { Write-Host '⚠️ npm не найден или недоступен' }"

echo.
echo ========================================
echo    📋 Рекомендации
echo ========================================
echo.
echo 💡 Если npm не найден:
echo    1. Переустановите Node.js
echo    2. Выберите LTS версию
echo    3. Отметьте "Add to PATH" при установке
echo.
echo 💡 Если npm найден, но медленно работает:
echo    1. Используйте быстрый запуск (опция 2 в меню)
echo    2. Или запустите VRM вручную
echo.
pause 
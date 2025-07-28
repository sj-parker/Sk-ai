@echo off
chcp 65001 >nul
title Диагностика проблем

echo.
echo ========================================
echo    🔍 Диагностика проблем системы
echo ========================================
echo.

echo 📋 Проверка компонентов:
echo.

:: Python
echo 🔍 Python:
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден
) else (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ Python: %%i
)

:: Node.js
echo.
echo 🔍 Node.js:
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js не найден
) else (
    for /f "tokens=*" %%i in ('node --version') do echo ✅ Node.js: %%i
)

:: npm
echo.
echo 🔍 npm:
timeout /t 2 /nobreak >nul
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm не найден или зависает
) else (
    for /f "tokens=*" %%i in ('npm --version') do echo ✅ npm: %%i
)

:: Папки
echo.
echo 🔍 Структура проекта:
if exist "assistant" (
    echo ✅ Папка assistant найдена
) else (
    echo ❌ Папка assistant не найдена
)

if exist "VRMoverlay" (
    echo ✅ Папка VRMoverlay найдена
) else (
    echo ❌ Папка VRMoverlay не найдена
)

:: Виртуальное окружение
echo.
echo 🔍 Python окружение:
if exist "assistant\venv" (
    echo ✅ Виртуальное окружение найдено
) else (
    echo ❌ Виртуальное окружение не найдено
)

:: Node modules
echo.
echo 🔍 Node.js зависимости:
if exist "VRMoverlay\node_modules" (
    echo ✅ node_modules найдены
) else (
    echo ❌ node_modules не найдены
)

:: Порты
echo.
echo 🔍 Проверка портов:
netstat -an | findstr :3000 >nul && echo ✅ Порт 3000 (VRM) занят || echo ❌ Порт 3000 (VRM) свободен
netstat -an | findstr :31991 >nul && echo ✅ Порт 31991 (Overlay) занят || echo ❌ Порт 31991 (Overlay) свободен
netstat -an | findstr :31992 >nul && echo ✅ Порт 31992 (WebSocket) занят || echo ❌ Порт 31992 (WebSocket) свободен
netstat -an | findstr :31994 >nul && echo ✅ Порт 31994 (Мониторинг) занят || echo ❌ Порт 31994 (Мониторинг) свободен

echo.
echo ========================================
echo    📋 Рекомендации
echo ========================================
echo.

:: Рекомендации на основе диагностики
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Установите Python: https://www.python.org/downloads/
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Установите Node.js: https://nodejs.org/
)

if not exist "assistant\venv" (
    echo 💡 Создайте виртуальное окружение: cd assistant && python -m venv venv
)

if not exist "VRMoverlay\node_modules" (
    echo 💡 Установите npm пакеты: cd VRMoverlay && npm install
)

echo.
echo 💡 Для запуска только ассистента: start_assistant_only.bat
echo 💡 Для ручного запуска VRM: start_vrm_manual.bat
echo.
pause 
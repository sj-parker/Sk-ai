@echo off
chcp 65001 >nul
title Остановка VRM + Ассистент

echo.
echo ========================================
echo    🛑 Остановка системы
echo ========================================
echo.

:: Завершаем процессы Python
echo 🔍 Завершение процессов Python...
taskkill /F /IM python.exe /T >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Процессы Python не найдены
) else (
    echo ✅ Процессы Python остановлены
)

:: Завершаем процессы Node.js
echo 🔍 Завершение процессов Node.js...
taskkill /F /IM node.exe /T >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Процессы Node.js не найдены
) else (
    echo ✅ Процессы Node.js остановлены
)

:: Завершаем процессы cmd, запущенные нашими скриптами
echo 🔍 Завершение окон терминалов...
wmic process where "commandline like '%%VRM%%' and name='cmd.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%Ассистент%%' and name='cmd.exe'" call terminate >nul 2>&1

echo.
echo ========================================
echo    ✅ Система остановлена!
echo ========================================
echo.

timeout /t 2 /nobreak >nul 
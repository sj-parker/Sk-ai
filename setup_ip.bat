@echo off
chcp 65001 >nul
title Настройка IP адреса

echo.
echo ========================================
echo    🔧 Настройка IP адреса
echo ========================================
echo.

:: Получаем текущий IP адрес
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "current_ip=%%a"
    set "current_ip=!current_ip: =!"
    goto :found_ip
)

:found_ip
echo 🔍 Текущий IP адрес: %current_ip%
echo.

:: Показываем текущие настройки
echo 📋 Текущие настройки:
echo.

if exist "assistant\config.yaml" (
    echo Ассистент (config.yaml):
    findstr "OVERLAY_WS_HOST" assistant\config.yaml
) else (
    echo ❌ Файл assistant\config.yaml не найден
)

echo.
if exist "VRMoverlay\src\vrm-websocket.js" (
    echo VRM (vrm-websocket.js):
    findstr "wsHost" VRMoverlay\src\vrm-websocket.js
) else (
    echo ❌ Файл VRMoverlay\src\vrm-websocket.js не найден
)

echo.
echo ========================================
echo.

:: Спрашиваем пользователя
set /p new_ip="Введите новый IP адрес (или Enter для %current_ip%): "
if "%new_ip%"=="" set "new_ip=%current_ip%"

echo.
echo 🔧 Обновление конфигурации...

:: Обновляем config.yaml
if exist "assistant\config.yaml" (
    echo 📝 Обновление assistant\config.yaml...
    powershell -Command "(Get-Content 'assistant\config.yaml') -replace 'OVERLAY_WS_HOST: .*', 'OVERLAY_WS_HOST: \"%new_ip%\"' | Set-Content 'assistant\config.yaml'"
    powershell -Command "(Get-Content 'assistant\config.yaml') -replace 'OVERLAY_WS_HOST: .*', 'OVERLAY_WS_HOST: \"%new_ip%\"' | Set-Content 'assistant\config.yaml'"
    echo ✅ assistant\config.yaml обновлен
) else (
    echo ❌ Файл assistant\config.yaml не найден
)

:: Обновляем vrm-websocket.js
if exist "VRMoverlay\src\vrm-websocket.js" (
    echo 📝 Обновление VRMoverlay\src\vrm-websocket.js...
    powershell -Command "(Get-Content 'VRMoverlay\src\vrm-websocket.js') -replace 'this\.wsHost = .*', 'this.wsHost = ''%new_ip%'';' | Set-Content 'VRMoverlay\src\vrm-websocket.js'"
    echo ✅ VRMoverlay\src\vrm-websocket.js обновлен
) else (
    echo ❌ Файл VRMoverlay\src\vrm-websocket.js не найден
)

echo.
echo ========================================
echo    ✅ Настройка завершена
echo ========================================
echo.
echo 🔧 Новый IP адрес: %new_ip%
echo.
echo 💡 Теперь можно запускать систему:
echo 💡 start_vrm_assistant.bat
echo.
pause 
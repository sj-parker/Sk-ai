@echo off
echo Запуск аудио стрим сервера...
cd /d "%~dp0"
python audio_stream_server.py
pause 
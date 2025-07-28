from multiprocessing import Process
import asyncio
import threading
import os
import glob
import json
import time
import logging

from recognize_from_microphone import recognize_from_microphone_async
from audio_output import chat_stream_ollama
from telegram_bot import run_telegram_bot
from overlay_server import start_overlay_server, find_free_port, send_text_to_overlay, send_to_overlay
from web_overlay.web_server import app as overlay_app
from memory.user_context import get_user_context, save_user_memory, save_persistent_memory
from twitch_youtube_chat import run_all_chats
from monitor import start_monitor_thread, error_log, module_status, sanitize_user_input
from config import get, check_required_config
from ocr_module import start_ocr_monitoring, stop_ocr_monitoring
from triggers import contains_trigger, is_mention_required
from auto_activity import start_auto_activity, stop_auto_activity

# Импорт аудио стрим сервера
try:
    from audio_stream_server import start_audio_stream
    AUDIO_STREAM_AVAILABLE = True
    print("[AUDIO STREAM] Модуль аудио стрима доступен")
except ImportError as e:
    AUDIO_STREAM_AVAILABLE = False
    print(f"[AUDIO STREAM] Модуль аудио стрима недоступен: {e}")

# Настройка логирования
def setup_logging():
    log_config = get('LOGGING', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    
    # Настройка основного логгера
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Отключение отладочных логов для внешних библиотек
    if not log_config.get('telegram_debug', False):
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    if not log_config.get('websocket_debug', False):
        logging.getLogger('websockets').setLevel(logging.WARNING)
    
    if not log_config.get('http_debug', False):
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

# Уникальный пользователь для локального чата
memory, role_manager = get_user_context("local", 'local')

# Ищем свободный порт для WebSocket сервера
overlay_ws_host = get('OVERLAY_WS_HOST', '0.0.0.0')
overlay_ws_port = get('OVERLAY_WS_PORT', 31992)
overlay_client_host = get('OVERLAY_CLIENT_HOST', '192.168.1.4')
overlay_app.config['OVERLAY_WS_PORT'] = overlay_ws_port  # для index.html
overlay_app.config['OVERLAY_WS_HOST'] = overlay_ws_host # для index.html
overlay_app.config['OVERLAY_CLIENT_HOST'] = overlay_client_host # для клиента (браузера)
overlay_app.config['TEXT_OVERLAY_WS_PORT'] = overlay_ws_port + 1  # для text_overlay.html

def run_overlay_web():
    host = get('OVERLAY_HOST', '0.0.0.0')
    port = get('OVERLAY_PORT', 31991)
    overlay_app.run(host=host, port=port)

# Запуск Flask в отдельном потоке
threading.Thread(target=run_overlay_web, daemon=True).start()

async def run_local_chat():
    # Запускаем WebSocket overlay-сервер
    overlay_task = asyncio.create_task(start_overlay_server(overlay_ws_port, host=overlay_ws_host, text_port=overlay_ws_port + 1))
    
    # Ждем немного, чтобы сервер успел запуститься
    await asyncio.sleep(1)

    print("🧠 Голосовой ассистент запущен. Говорите...")
    try:
        while True:
            user_text = await recognize_from_microphone_async()
            if user_text:
                user_text = sanitize_user_input(user_text)
                if is_mention_required('local_voice') and not contains_trigger(user_text):
                    print("[Фильтр]: Нет триггера в голосовом вводе, игнорируется.")
                    continue
                print(f"\n[Вы сказали]: {user_text}")
                await send_to_overlay("waiting")
                
                # Выбираем бэкенд из конфига
                llm_backend = get('LLM', {}).get('backend', 'ollama')
                if llm_backend == 'llamacpp':
                    from audio_output import chat_stream_llamacpp
                    llm_config = get('LLM', {}).get('llamacpp', {})
                    await chat_stream_llamacpp(
                        role_manager, 
                        memory, 
                        user_text,
                        model_path=llm_config.get('model_path'),
                        speak=True
                    )
                else:
                    from audio_output import chat_stream_ollama
                    ollama_config = get('LLM', {}).get('ollama', {})
                    await chat_stream_ollama(
                        role_manager, 
                        memory, 
                        user_text,
                        model_name=ollama_config.get('model', 'gemma3n:e2b'),
                        speak=True,
                        user_name="Буу"
                    )
            else:
                print("\n[Не удалось распознать речь]")
    except asyncio.CancelledError:
        print("\n[Локальный чат остановлен]")
    finally:
        save_user_memory("local")

async def main_async():
    # Запускаем аудио стрим сервер, если доступен
    audio_task = None
    if AUDIO_STREAM_AVAILABLE:
        audio_task = asyncio.create_task(start_audio_stream())
        print("[AUDIO STREAM] Аудио стрим сервер запущен")
    
    # Запускаем автоматическую активность в асинхронном контексте
    start_auto_activity()
    print("[AUTO ACTIVITY] Автоматическая активность запущена")
    
    await asyncio.gather(
        run_local_chat(),
        run_all_chats(),
    )

def telegram_proc():
    try:
        print('[MAIN] Telegram process: старт')
        module_status['telegram'] = True
        run_telegram_bot()
        print('[MAIN] Telegram process: завершён')
    except Exception as e:
        print(f'[TelegramBot Error]: {e}')
        error_log.append({'error': f'[TelegramBot Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})
        module_status['telegram'] = False

def main():
    # Настройка логирования
    setup_logging()
    
    # Проверка обязательных параметров конфига при старте
    check_required_config()
    
    # Запускаем Telegram-бота в отдельном процессе, если разрешено
    ENABLE_TELEGRAM = get('ENABLE_TELEGRAM', True)
    ENABLE_SPEECH_RECOGNITION = get('ENABLE_SPEECH_RECOGNITION', True)
    ENABLE_OCR = get('ENABLE_OCR', True)
    p = None
    if ENABLE_TELEGRAM:
        print('[MAIN] Перед запуском процесса Telegram')
        p = Process(target=telegram_proc)
        p.start()
        print('[MAIN] После запуска процесса Telegram')
    else:
        print('[MAIN] Telegram модуль отключён через конфиг.')
    
    # Запускаем OCR модуль, если разрешено
    if ENABLE_OCR:
        print('[MAIN] Запуск OCR модуля')
        ocr_source = get('OCR_SOURCE', 'screen')
        ocr_interval = get('OCR_INTERVAL', 5)
        start_ocr_monitoring(ocr_source, ocr_interval)
    else:
        print('[MAIN] OCR модуль отключён через конфиг.')
    
    try:
        start_monitor_thread()
        
        if ENABLE_SPEECH_RECOGNITION:
            asyncio.run(main_async())
        else:
            print('[MAIN] Модуль распознавания речи отключён через конфиг.')
            while True:
                time.sleep(60)
    except KeyboardInterrupt:
        print("\n[Завершение программы по Ctrl+C]")
    except Exception as e:
        print(f'[LocalChat Error]: {e}')
        error_log.append({'error': f'[LocalChat Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})
    finally:
        print('[MAIN] Завершаем процесс Telegram')
        if p:
            p.terminate()
            p.join()
        print('[MAIN] Останавливаем OCR модуль')
        stop_ocr_monitoring()
        print('[MAIN] Останавливаем автоматическую активность')
        stop_auto_activity()

# --- Пример функции для ежедневного сохранения persistent памяти ---
def save_all_users_persistent_memory():
    users_dir = os.path.join(os.path.dirname(__file__), 'memory', 'users')
    for filename in os.listdir(users_dir):
        if filename.endswith('.json'):
            user_id = filename.replace('.json', '')
            filepath = os.path.join(users_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                save_persistent_memory(user_id, messages)
            except Exception as e:
                print(f"[Ошибка сохранения persistent памяти для {user_id}]: {e}")

if __name__ == "__main__":
    main()

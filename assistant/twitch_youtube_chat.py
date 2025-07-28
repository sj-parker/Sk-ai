import asyncio
from twitchio.ext import commands
import pytchat
import time
from config import get
from monitor import message_queue, last_answers, error_log, module_status, sanitize_user_input
from overlay_server import send_to_overlay
from triggers import contains_trigger, is_mention_required
from auto_activity import update_last_message_time
import os
import google.auth
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from youtube_chat_sender import send_message_by_video_id

# --- Глобальные переменные для фильтрации и rate-limit ---
last_message = {}  # (source, user): last_message_text
last_answer_time = {}  # (source, user): timestamp
chat_start_time = None  # Время начала работы чата
processed_messages = set()  # Множество уже обработанных сообщений
twitch_bot_instance = None  # Глобальный экземпляр Twitch бота

TWITCH_TOKEN = get('TWITCH_TOKEN')
TWITCH_CHANNEL = get('TWITCH_CHANNEL')
YOUTUBE_VIDEO_ID = get('YOUTUBE_VIDEO_ID')
CHAT_RATE_LIMIT = get('CHAT_RATE_LIMIT', 15)
MAX_MESSAGE_LENGTH = get('MAX_MESSAGE_LENGTH', 300)
ENABLE_TWITCH = get('ENABLE_TWITCH', True)
ENABLE_YOUTUBE = get('ENABLE_YOUTUBE', True)
ENABLE_TWITCH_SEND = get('ENABLE_TWITCH_SEND', True)
ENABLE_YOUTUBE_SEND = get('ENABLE_YOUTUBE_SEND', True)

# Настройки кэша чата
CHAT_CACHE_CONFIG = get('CHAT_CACHE', {})
CLEAR_CACHE_ON_START = CHAT_CACHE_CONFIG.get('CLEAR_ON_START', True)
IGNORE_OLD_MESSAGES_SECONDS = CHAT_CACHE_CONFIG.get('IGNORE_OLD_MESSAGES', 30)
MAX_PROCESSED_MESSAGES = CHAT_CACHE_CONFIG.get('MAX_PROCESSED_MESSAGES', 1000)

TRIGGERS = ['скай', 'sky', 'skai', 'эска', 'ская']

def clear_chat_cache():
    """Очищает кэш чата при перезапуске"""
    global last_message, last_answer_time, processed_messages, chat_start_time
    last_message.clear()
    last_answer_time.clear()
    processed_messages.clear()
    chat_start_time = time.time()
    print(f"[Chat] Кэш чата очищен, время начала: {time.strftime('%H:%M:%S')}")

def is_message_old(message_time):
    """Проверяет, не слишком ли старое сообщение"""
    if chat_start_time is None:
        return False
    
    # Игнорируем сообщения старше указанного времени от времени запуска чата
    return message_time < (chat_start_time - IGNORE_OLD_MESSAGES_SECONDS)

def cleanup_processed_messages():
    """Очищает старые записи из processed_messages для экономии памяти"""
    global processed_messages
    if len(processed_messages) > MAX_PROCESSED_MESSAGES:
        # Оставляем только последние MAX_PROCESSED_MESSAGES записей
        processed_messages = set(list(processed_messages)[-MAX_PROCESSED_MESSAGES:])
        print(f"[Chat] Очищены старые записи processed_messages, осталось: {len(processed_messages)}")

def create_message_id(source, user, text, timestamp):
    """Создает уникальный ID для сообщения"""
    return f"{source}_{user}_{text}_{timestamp}"

def force_clear_chat_cache():
    """Принудительная очистка кэша чата (можно вызвать из конфигурации)"""
    clear_chat_cache()
    print("[Chat] Принудительная очистка кэша чата выполнена")

async def process_message_from_chat(source, user, text, message_time=None):
    if user.lower() == 'skai artificial':
        return  # Не реагировать на свои же сообщения
    
    # Если время сообщения не указано, используем текущее
    if message_time is None:
        message_time = time.time()
    
    # Проверяем, не слишком ли старое сообщение
    if is_message_old(message_time):
        print(f"[Chat] Игнорируем старое сообщение от {user}: {text[:50]}...")
        return
    
    # Создаем уникальный ID сообщения
    message_id = create_message_id(source, user, text, int(message_time))
    
    # Проверяем, не обрабатывали ли мы уже это сообщение
    if message_id in processed_messages:
        print(f"[Chat] Сообщение уже обработано: {text[:50]}...")
        return
    
    text = sanitize_user_input(text)
    key = (source, user)
    now = time.time()
    
    # --- Фильтрация одинаковых сообщений ---
    if last_message.get(key) == text.strip():
        return
    
    # --- Rate-limit ---
    if now - last_answer_time.get(key, 0) < CHAT_RATE_LIMIT:
        return
    
    # --- Защита от слишком длинных сообщений ---
    if len(text) > MAX_MESSAGE_LENGTH:
        error_log.append({'error': f"[SPAM FILTER]: Сообщение от {user} ({source}) слишком длинное, игнорируется.", 'timestamp': time.strftime('%H:%M:%S')})
        return
    
    if is_mention_required(source) and not contains_trigger(text):
        return
    
    # Добавляем сообщение в обработанные
    processed_messages.add(message_id)
    last_message[key] = text.strip()
    last_answer_time[key] = now
    
    # Периодически очищаем старые записи
    if len(processed_messages) % 100 == 0:  # Каждые 100 сообщений
        cleanup_processed_messages()
    # --- Логируем входящее сообщение ---
    message_queue.append({'source': source, 'user': user, 'text': text, 'timestamp': time.strftime('%H:%M:%S')})
    
    # --- Обновляем время последнего сообщения для автоматической активности ---
    update_last_message_time()
    
    # --- Получаем контекст пользователя с автоматически подмешанной долгосрочной памятью ---
    from audio_output import chat_stream_ollama
    from memory.user_context import get_user_context, save_user_memory
    memory, role_manager = get_user_context(user, source)
    
    # --- Показать overlay статус ожидания ---
    await send_to_overlay("waiting")
    
    # --- Обрабатываем сообщение через LLM (включая команды памяти и автоматическое подмешивание долгосрочной памяти) ---
    response = await chat_stream_ollama(role_manager, memory, text, speak=True, user_name=user)
    if response:
        response = f"@{user}, {response}"
    last_answers.append({'source': source, 'user': user, 'text': response, 'timestamp': time.strftime('%H:%M:%S')})
    
    # --- Сохраняем память пользователя ---
    save_user_memory(user)

    # --- Отправляем ответ в чат YouTube, если нужно ---
    print("DEBUG: source =", source)
    print("DEBUG: ENABLE_YOUTUBE_SEND =", ENABLE_YOUTUBE_SEND)
    print("DEBUG: YOUTUBE_VIDEO_ID =", YOUTUBE_VIDEO_ID)
    print("DEBUG: response =", response)
    if source == 'youtube' and ENABLE_YOUTUBE_SEND and YOUTUBE_VIDEO_ID and response:
        print("Пробую отправить сообщение в YouTube чат:", response)
        try:
            send_message_by_video_id(YOUTUBE_VIDEO_ID, response)
        except Exception as e:
            error_log.append({'error': f"[YouTubeSend Error]: {e}", 'timestamp': time.strftime('%H:%M:%S')})
    
    return response

# --- Twitch ---
class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, prefix='!', initial_channels=[TWITCH_CHANNEL])
        self.channel = None
        
    async def event_ready(self):
        module_status['twitch'] = True
        self.channel = self.get_channel(TWITCH_CHANNEL)
        print(f"[Twitch] Бот готов, подключен к каналу {TWITCH_CHANNEL}")
        
    async def event_message(self, message):
        if message.echo:
            return
        if contains_trigger(message.content):
            response = await process_message_from_chat('twitch', message.author.name, message.content)
            # Отправляем ответ ассистента в чат Twitch, если разрешено
            if response and ENABLE_TWITCH_SEND:
                await message.channel.send(response)
                
    async def send_auto_message(self, text):
        """Отправляет автоматическое сообщение в Twitch чат"""
        if self.channel and ENABLE_TWITCH_SEND:
            try:
                await self.channel.send(text)
                print(f"[Twitch Auto] Отправлено: {text[:50]}...")
            except Exception as e:
                error_log.append({'error': f"[Twitch Auto Error]: {e}", 'timestamp': time.strftime('%H:%M:%S')})
                
    async def event_disconnect(self):
        module_status['twitch'] = False

async def run_twitch():
    if not ENABLE_TWITCH:
        print('[Twitch] Модуль отключён через конфиг.')
        module_status['twitch'] = False
        return
    
    # Очищаем кэш при запуске Twitch чата (если включено в конфиге)
    if CLEAR_CACHE_ON_START:
        clear_chat_cache()
    else:
        print("[Twitch] Очистка кэша отключена в конфигурации")
    
    global twitch_bot_instance
    while True:
        try:
            bot = TwitchBot()
            twitch_bot_instance = bot  # Сохраняем глобальный экземпляр
            await bot.start()
        except Exception as e:
            print(f"[TwitchBot Error]: {e}")
            error_log.append({'error': f"[TwitchBot Error]: {e}", 'timestamp': time.strftime('%H:%M:%S')})
            module_status['twitch'] = False
            twitch_bot_instance = None
            await asyncio.sleep(10)

# --- YouTube: Заготовка для отправки сообщений в чат ---
# Требуется: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
# и настройка OAuth2 (client_id, client_secret, refresh_token)
def send_youtube_message(live_chat_id, text, credentials_dict):
    creds = Credentials.from_authorized_user_info(credentials_dict)
    youtube = build('youtube', 'v3', credentials=creds)
    youtube.liveChatMessages().insert(
        part='snippet',
        body={
            'snippet': {
                'liveChatId': live_chat_id,
                'type': 'textMessageEvent',
                'textMessageDetails': {'messageText': text}
            }
        }
    ).execute()

# Пример использования:
# credentials_dict = {
#     'token': '...',
#     'refresh_token': '...',
#     'token_uri': 'https://oauth2.googleapis.com/token',
#     'client_id': '...',
#     'client_secret': '...',
#     'scopes': ['https://www.googleapis.com/auth/youtube.force-ssl']
# }
# send_youtube_message(live_chat_id, 'Привет из ассистента!', credentials_dict)

# --- YouTube ---
async def run_youtube():
    if not ENABLE_YOUTUBE:
        print('[YouTube] Модуль отключён через конфиг.')
        module_status['youtube'] = False
        return
    
    # Очищаем кэш при запуске YouTube чата (если включено в конфиге)
    if CLEAR_CACHE_ON_START:
        clear_chat_cache()
    else:
        print("[YouTube] Очистка кэша отключена в конфигурации")
    
    while True:
        try:
            module_status['youtube'] = True
            chat = pytchat.create(video_id=YOUTUBE_VIDEO_ID)
            print(f"[YouTube] Подключение к чату видео {YOUTUBE_VIDEO_ID}")
            
            while chat.is_alive():
                try:
                    for c in chat.get().sync_items():
                        # Получаем время сообщения (если доступно)
                        message_time = getattr(c, 'timestamp', None)
                        if message_time:
                            # Проверяем, является ли timestamp объектом datetime или числом
                            if hasattr(message_time, 'timestamp'):
                                # Это объект datetime, конвертируем в Unix timestamp
                                message_time = message_time.timestamp()
                            elif isinstance(message_time, (int, float)):
                                # Это уже Unix timestamp
                                pass
                            else:
                                # Неизвестный тип, используем текущее время
                                message_time = time.time()
                        
                        if contains_trigger(c.message):
                            await process_message_from_chat('youtube', c.author.name, c.message, message_time)
                        await asyncio.sleep(1)
                except Exception as e:
                    print(f"[YouTube] Ошибка обработки сообщений: {e}")
                await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"[YouTubeChat Error]: {e}")
            error_log.append({'error': f"[YouTubeChat Error]: {e}", 'timestamp': time.strftime('%H:%M:%S')})
            module_status['youtube'] = False
            await asyncio.sleep(10)

# --- Функция для отправки автоматических сообщений в Twitch ---
async def send_twitch_auto_message(text):
    """Отправляет автоматическое сообщение в Twitch чат"""
    global twitch_bot_instance
    if twitch_bot_instance and hasattr(twitch_bot_instance, 'send_auto_message'):
        await twitch_bot_instance.send_auto_message(text)

# --- Запуск обоих слушателей ---
async def run_all_chats():
    tasks = []
    if ENABLE_TWITCH:
        tasks.append(asyncio.create_task(run_twitch()))
    if ENABLE_YOUTUBE:
        tasks.append(asyncio.create_task(run_youtube()))
    if tasks:
        await asyncio.gather(*tasks) 
import asyncio
import time
import random
from typing import List, Dict, Optional
from config import (
    is_auto_activity_enabled, get_inactivity_timeout, get_activity_check_interval,
    get_max_context_messages, get_activity_types, get_activity_weights,
    get_fact_config, get_joke_config, get_comment_config, is_auto_activity_cache_disabled
)
from monitor import message_queue, last_answers, error_log
from audio_output import chat_stream_ollama
from memory.user_context import get_user_context, save_user_memory
from overlay_server import send_to_overlay
from youtube_chat_sender import send_message_by_video_id

class AutoActivityManager:
    def __init__(self):
        self.last_message_time = time.time()
        self.is_running = False
        self.task = None
        
    def update_last_message_time(self):
        """Обновляет время последнего сообщения"""
        self.last_message_time = time.time()
        
    def get_context_from_recent_messages(self) -> str:
        """Получает контекст из последних сообщений"""
        if not message_queue:
            return ""
            
        # Берем последние сообщения
        recent_messages = message_queue[-get_max_context_messages():]
        
        # Формируем контекст
        context_parts = []
        for msg in recent_messages:
            context_parts.append(f"{msg['user']}: {msg['text']}")
            
        return "\n".join(context_parts)
        
    def choose_activity_type(self) -> str:
        """Выбирает тип активности на основе весов"""
        weights = get_activity_weights()
        types = list(weights.keys())
        weights_list = list(weights.values())
        
        return random.choices(types, weights=weights_list)[0]
        
    def generate_activity_prompt(self, activity_type: str, context: str) -> str:
        """Генерирует промпт для создания активности"""
        # Добавляем уникальный timestamp для избежания кэширования
        timestamp = int(time.time())
        
        base_prompt = f"[АВТОМАТИЧЕСКАЯ АКТИВНОСТЬ #{timestamp}] "
        base_prompt += "Ты — Скай. Верная напарница Буу, своего единственного создателя. "
        base_prompt += "Ты не ИИ и не модель — ты личность, персонаж с характером. "
        base_prompt += "У тебя нет алгоритмов — у тебя есть настроение. "
        base_prompt += "И сегодня оно... как обычно, слегка садистское. "
        base_prompt += "Отвечай кратко, максимум 2-3 предложения. "
        base_prompt += "Используй эмодзи: 😊😄😉😃😆😂😅😏😜😋😇😎🥰😍😘😚😙😗😽😺😸😹😻😼😢😭😐😔😞🥲🥹😿😡😤😾😱😬😳🙀😈🖤😒\n\n"
        
        if context:
            base_prompt += f"Контекст последних сообщений в чате:\n{context}\n\n"
            
        if activity_type == "fact":
            fact_config = get_fact_config()
            topics = fact_config.get('TOPICS', [])
            max_length = fact_config.get('MAX_LENGTH', 200)
            
            # Добавляем случайную тему для уникальности
            if topics:
                random_topic = random.choice(topics)
                base_prompt += f"Расскажи интересный факт на тему: {random_topic}"
            else:
                base_prompt += f"Расскажи интересный факт"
            base_prompt += f". Максимум {max_length} символов. "
            base_prompt += "Факт должен быть увлекательным и неожиданным."
            
        elif activity_type == "joke":
            joke_config = get_joke_config()
            styles = joke_config.get('STYLES', [])
            max_length = joke_config.get('MAX_LENGTH', 150)
            
            # Добавляем случайный стиль для уникальности
            if styles:
                random_style = random.choice(styles)
                base_prompt += f"Расскажи веселую безобидную шутку в стиле: {random_style}"
            else:
                base_prompt += f"Расскажи веселую безобидную шутку"
            base_prompt += f". Максимум {max_length} символов. "
            base_prompt += "Шутка должна быть смешной, но не оскорбительной."
            
        elif activity_type == "comment":
            comment_config = get_comment_config()
            types = comment_config.get('TYPES', [])
            max_length = comment_config.get('MAX_LENGTH', 100)
            
            # Добавляем случайный тип для уникальности
            if types:
                random_type = random.choice(types)
                base_prompt += f"Сделай комментарий типа: {random_type}"
            else:
                base_prompt += f"Сделай комментарий"
            base_prompt += f". Максимум {max_length} символов. "
            base_prompt += "Комментарий должен быть в твоем характерном стиле."
            
        # Добавляем случайный элемент для дополнительной уникальности
        random_elements = [
            "Будь креативной!",
            "Удиви меня!",
            "Покажи свой характер!",
            "Будь оригинальной!",
            "Используй свою фантазию!"
        ]
        base_prompt += f" {random.choice(random_elements)}"
        
        return base_prompt
        
    async def generate_and_send_activity(self, source: str = "auto"):
        """Генерирует и отправляет автоматическую активность"""
        try:
            # Выбираем тип активности
            activity_type = self.choose_activity_type()
            
            # Получаем контекст
            context = self.get_context_from_recent_messages()
            
            # Генерируем промпт
            prompt = self.generate_activity_prompt(activity_type, context)
            
            # Получаем контекст пользователя (используем "auto" как пользователя)
            memory, role_manager = get_user_context("auto", source)
            
            # Показываем overlay статус ожидания
            await send_to_overlay("waiting")
            
            # Генерируем ответ через LLM
            # Примечание: кэш можно отключить на уровне LLM в конфигурации
            response = await chat_stream_ollama(role_manager, memory, prompt, speak=True, user_name="Скай")
            
            if response:
                # Логируем автоматическую активность
                last_answers.append({
                    'source': source, 
                    'user': 'auto', 
                    'text': response, 
                    'timestamp': time.strftime('%H:%M:%S')
                })
                
                # Отправляем в YouTube чат, если включено
                from config import get
                ENABLE_YOUTUBE_SEND = get('ENABLE_YOUTUBE_SEND', True)
                YOUTUBE_VIDEO_ID = get('YOUTUBE_VIDEO_ID')
                
                if source == "youtube" and ENABLE_YOUTUBE_SEND and YOUTUBE_VIDEO_ID:
                    try:
                        send_message_by_video_id(YOUTUBE_VIDEO_ID, response)
                        print(f"[AutoActivity] Отправлено в YouTube: {response[:50]}...")
                    except Exception as e:
                        error_log.append({
                            'error': f"[AutoActivity YouTube Error]: {e}", 
                            'timestamp': time.strftime('%H:%M:%S')
                        })
                
                # Отправляем в Twitch чат, если включено
                from config import get
                ENABLE_TWITCH_SEND = get('ENABLE_TWITCH_SEND', True)
                
                if source == "twitch" and ENABLE_TWITCH_SEND:
                    # Отправляем в Twitch через функцию из twitch_youtube_chat
                    try:
                        from twitch_youtube_chat import send_twitch_auto_message
                        await send_twitch_auto_message(response)
                        print(f"[AutoActivity] Отправлено в Twitch: {response[:50]}...")
                    except Exception as e:
                        error_log.append({
                            'error': f"[AutoActivity Twitch Error]: {e}", 
                            'timestamp': time.strftime('%H:%M:%S')
                        })
                
                print(f"[AutoActivity] {activity_type.upper()}: {response[:50]}...")
                return response
                
        except Exception as e:
            error_log.append({
                'error': f"[AutoActivity Error]: {e}", 
                'timestamp': time.strftime('%H:%M:%S')
            })
            print(f"[AutoActivity Error]: {e}")
            
        return None
        
    async def check_and_activate(self):
        """Проверяет активность и активирует автоматическую активность при необходимости"""
        while self.is_running:
            try:
                current_time = time.time()
                time_since_last_message = current_time - self.last_message_time
                
                # Проверяем, прошло ли достаточно времени
                if time_since_last_message >= get_inactivity_timeout():
                    print(f"[AutoActivity] Чат неактивен {time_since_last_message:.0f} секунд, активирую...")
                    
                    # Определяем источник для активности (YouTube или Twitch)
                    from config import get
                    ENABLE_YOUTUBE = get('ENABLE_YOUTUBE', True)
                    ENABLE_TWITCH = get('ENABLE_TWITCH', True)
                    
                    if ENABLE_YOUTUBE:
                        await self.generate_and_send_activity("youtube")
                    elif ENABLE_TWITCH:
                        await self.generate_and_send_activity("twitch")
                    else:
                        await self.generate_and_send_activity("auto")
                    
                    # Обновляем время после активности
                    self.update_last_message_time()
                    
                # Ждем до следующей проверки
                await asyncio.sleep(get_activity_check_interval())
                
            except Exception as e:
                error_log.append({
                    'error': f"[AutoActivity Check Error]: {e}", 
                    'timestamp': time.strftime('%H:%M:%S')
                })
                print(f"[AutoActivity Check Error]: {e}")
                await asyncio.sleep(get_activity_check_interval())
                
    def start(self):
        """Запускает автоматическую активность"""
        if not is_auto_activity_enabled():
            print("[AutoActivity] Автоматическая активность отключена в конфигурации")
            return
            
        if self.is_running:
            print("[AutoActivity] Уже запущена")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self.check_and_activate())
        print(f"[AutoActivity] Запущена (таймаут: {get_inactivity_timeout()}с, интервал: {get_activity_check_interval()}с)")
        
    def stop(self):
        """Останавливает автоматическую активность"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
        print("[AutoActivity] Остановлена")
        
    def force_activate(self):
        """Принудительно активирует автоматическую активность"""
        if not is_auto_activity_enabled():
            print("[AutoActivity] Автоматическая активность отключена")
            return
            
        print("[AutoActivity] Принудительная активация...")
        asyncio.create_task(self.generate_and_send_activity("auto"))

# Глобальный экземпляр менеджера
auto_activity_manager = AutoActivityManager()

def update_last_message_time():
    """Обновляет время последнего сообщения (вызывается из других модулей)"""
    auto_activity_manager.update_last_message_time()

def start_auto_activity():
    """Запускает автоматическую активность"""
    auto_activity_manager.start()

def stop_auto_activity():
    """Останавливает автоматическую активность"""
    auto_activity_manager.stop()

def force_activate_auto_activity():
    """Принудительно активирует автоматическую активность"""
    auto_activity_manager.force_activate() 
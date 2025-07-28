#!/usr/bin/env python3
"""
Тестовый скрипт для проверки очистки кэша чата
"""

import time
from twitch_youtube_chat import clear_chat_cache, force_clear_chat_cache, processed_messages, chat_start_time

def test_chat_cache():
    print("🧪 Тестирование системы кэша чата")
    print("=" * 50)
    
    # Тест 1: Очистка кэша
    print("\n1️⃣ Тест очистки кэша:")
    print(f"   Время начала до очистки: {chat_start_time}")
    print(f"   Обработанных сообщений до очистки: {len(processed_messages)}")
    
    clear_chat_cache()
    
    print(f"   Время начала после очистки: {chat_start_time}")
    print(f"   Обработанных сообщений после очистки: {len(processed_messages)}")
    
    # Тест 2: Принудительная очистка
    print("\n2️⃣ Тест принудительной очистки:")
    force_clear_chat_cache()
    
    # Тест 3: Проверка настроек
    print("\n3️⃣ Проверка настроек кэша:")
    from config import get
    chat_cache_config = get('CHAT_CACHE', {})
    print(f"   CLEAR_ON_START: {chat_cache_config.get('CLEAR_ON_START', True)}")
    print(f"   IGNORE_OLD_MESSAGES: {chat_cache_config.get('IGNORE_OLD_MESSAGES', 30)} сек")
    print(f"   MAX_PROCESSED_MESSAGES: {chat_cache_config.get('MAX_PROCESSED_MESSAGES', 1000)}")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    test_chat_cache() 
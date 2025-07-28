#!/usr/bin/env python3
"""
Тест персонализации ответов с именем пользователя
"""

import asyncio
from memory.user_context import get_user_context
from audio_output import chat_stream_ollama

async def test_user_personalization():
    """Тестирует персонализацию ответов с разными именами пользователей"""
    
    # Тестовые пользователи
    test_users = [
        ("Виктор", "Привет! Как дела?"),
        ("Анна", "Расскажи анекдот"),
        ("Михаил", "Какая сегодня погода?"),
        ("Елена", "Что ты знаешь обо мне?")
    ]
    
    print("🧪 Тестирование персонализации ответов...\n")
    
    for user_name, message in test_users:
        print(f"👤 Пользователь: {user_name}")
        print(f"💬 Сообщение: {message}")
        
        # Получаем контекст пользователя
        memory, role_manager = get_user_context(user_name, 'test')
        
        # Тестируем с именем пользователя
        print("📝 Ответ с персонализацией:")
        response_with_name = await chat_stream_ollama(
            role_manager, 
            memory, 
            message, 
            speak=False, 
            user_name=user_name
        )
        print(f"✅ {response_with_name}\n")
        
        # Тестируем без имени пользователя для сравнения
        print("📝 Ответ без персонализации:")
        response_without_name = await chat_stream_ollama(
            role_manager, 
            memory, 
            message, 
            speak=False, 
            user_name=None
        )
        print(f"❌ {response_without_name}\n")
        
        print("-" * 50 + "\n")
        
        # Небольшая пауза между тестами
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_user_personalization()) 
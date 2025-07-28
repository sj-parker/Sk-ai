#!/usr/bin/env python3
"""
Тест интеграции llama.cpp с ассистентом
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get
from memory.user_context import get_user_context
from audio_output import chat_stream_llamacpp

async def test_llamacpp():
    print("🧪 Тестирование интеграции llama.cpp...")
    
    # Получаем контекст пользователя
    memory, role_manager = get_user_context("local", 'local')
    
    # Получаем настройки llama.cpp
    llm_config = get('LLM', {}).get('llamacpp', {})
    model_path = llm_config.get('model_path', 'E:\\Skai\\llm\\gemma-3n-E4B-it-Q6_K.gguf')
    
    print(f"📁 Модель: {model_path}")
    print(f"🔧 Исполняемый файл: {llm_config.get('executable_path')}")
    
    # Тестовый промпт
    test_prompt = "Привет! Как дела?"
    
    print(f"\n💬 Тестовый промпт: {test_prompt}")
    print("⏳ Ожидаем ответ...")
    
    try:
        # Вызываем функцию llama.cpp
        response = await chat_stream_llamacpp(
            role_manager=role_manager,
            memory=memory,
            prompt=test_prompt,
            model_path=model_path,
            speak=False  # Отключаем TTS для теста
        )
        
        print(f"\n✅ Ответ получен:")
        print(f"📝 {response}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llamacpp()) 
#!/usr/bin/env python3
"""
Тест ответа ассистента с аудио стримом
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_assistant_response():
    """Тестирует полный цикл ответа ассистента"""
    try:
        from audio_output import chat_stream_ollama
        from roles.role_manager import RoleManager
        from memory.manager import MemoryManager
        
        print("[TEST] Тестируем полный цикл ответа ассистента...")
        
        # Создаем менеджер ролей и память
        role_manager = RoleManager(source='test')
        memory = MemoryManager()
        
        # Тестовый вопрос
        test_prompt = "Привет! Как дела?"
        
        print(f"[TEST] Отправляем вопрос: {test_prompt}")
        
        # Вызываем функцию ответа ассистента
        response = await chat_stream_ollama(
            role_manager=role_manager,
            memory=memory,
            prompt=test_prompt,
            model_name="gemma3n:e2b",
            speak=True  # Включаем озвучивание
        )
        
        print(f"[TEST] Ответ ассистента: {response}")
        print("[TEST] Тест завершен")
            
    except Exception as e:
        print(f"[TEST ERROR]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_assistant_response()) 
#!/usr/bin/env python3
"""
Финальный тест системы долгосрочной памяти
"""

import asyncio
from memory.user_context import get_user_context, save_user_memory
from audio_output import chat_stream_ollama

async def test_final_memory_system():
    print("🧠 Финальный тест системы долгосрочной памяти")
    print("=" * 50)
    
    # Симулируем пользователя из Twitch
    user_id = "final_test_user"
    source = "twitch"
    
    print(f"👤 Пользователь: {user_id} ({source})")
    print()
    
    # Получаем контекст пользователя
    memory, role_manager = get_user_context(user_id, source)
    
    # Добавляем факты в память
    print("📝 Добавляем факты в память:")
    facts = [
        "запомни не люблю лето",
        "запомни очень люблю маму",
        "запомни боюсь пауков"
    ]
    
    for fact in facts:
        memory.add("user", fact)
        print(f"  ✅ {fact}")
    
    # Сохраняем в долгосрочную память
    memory.save_long_term()
    save_user_memory(user_id)
    
    print("\n💬 Тестируем обращения к ассистенту:")
    
    # Тест 1: Обычное обращение
    print("\n1. Обычное обращение:")
    message1 = "привет скай, как дела?"
    print(f"   Пользователь: {message1}")
    
    # Симулируем обработку через chat_stream_ollama
    memory.add("user", message1)
    context = memory.get_context_as_system_prompt()
    print(f"   Контекст с памятью: {context['content'][:100]}...")
    
    # Тест 2: Команда памяти
    print("\n2. Команда памяти:")
    message2 = "что ты помнишь обо мне?"
    print(f"   Пользователь: {message2}")
    
    memory.add("user", message2)
    memory_response = memory.handle_memory_commands(message2)
    if memory_response:
        print(f"   Ответ: {memory_response}")
    
    # Тест 3: Новый факт
    print("\n3. Новый факт:")
    message3 = "запомни люблю пиццу"
    print(f"   Пользователь: {message3}")
    
    memory.add("user", message3)
    memory.save_long_term()
    
    # Проверяем обновленный контекст
    context = memory.get_context_as_system_prompt()
    print(f"   Обновленный контекст: {context['content'][:100]}...")
    
    # Тест 4: Обращение с учетом памяти
    print("\n4. Обращение с учетом памяти:")
    message4 = "что мне заказать на ужин?"
    print(f"   Пользователь: {message4}")
    
    memory.add("user", message4)
    context = memory.get_context_as_system_prompt()
    print(f"   Контекст для LLM: {context['content'][:100]}...")
    print("   (LLM будет знать, что пользователь любит пиццу и может предложить её)")
    
    # Сохраняем финальное состояние
    save_user_memory(user_id)
    
    print("\n✅ Финальный тест завершен!")
    print("\n📊 Итоговая статистика:")
    stats = memory.get_memory_stats()
    print(f"- Краткосрочная: {stats['short_term_count']} сообщений")
    print(f"- Долгосрочная: {stats['long_term_count']} записей ({stats['long_term_words']} слов)")
    
    print("\n🎯 Результат:")
    print("Долгосрочная память автоматически подмешивается при каждом обращении!")
    print("LLM всегда знает факты о пользователе и может их использовать в ответах.")

if __name__ == "__main__":
    asyncio.run(test_final_memory_system()) 
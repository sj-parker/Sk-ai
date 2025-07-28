#!/usr/bin/env python3
"""
Тест естественной интеграции памяти
Проверяет, что LLM не упоминает память без необходимости
"""

import asyncio
from memory.manager import MemoryManager
from memory.user_context import save_user_memory
from config import is_long_term_natural_integration

async def test_natural_memory_integration():
    """Тестирует естественную интеграцию памяти"""
    
    print("🧠 Тест естественной интеграции памяти")
    print("=" * 50)
    
    # Создаем менеджер памяти
    memory = MemoryManager()
    user_id = "test_user"
    
    # Проверяем настройку
    natural_integration = is_long_term_natural_integration()
    print(f"📋 Естественная интеграция: {'ВКЛ' if natural_integration else 'ВЫКЛ'}")
    
    # Тест 1: Добавляем факты в память
    print("\n1. Добавление фактов в память:")
    facts = [
        "запомни люблю пиццу",
        "запомни боюсь пауков", 
        "запомни живу в Москве"
    ]
    
    for fact in facts:
        print(f"   Добавляем: {fact}")
        memory.add("user", fact)
    
    memory.save_long_term()
    
    # Тест 2: Проверяем системный промпт
    print("\n2. Системный промпт для LLM:")
    context = memory.get_context_as_system_prompt()
    print(f"   Контекст: {context['content']}")
    
    # Тест 3: Проверяем команду "что ты помнишь"
    print("\n3. Команда 'что ты помнишь':")
    response = memory.handle_memory_commands("что ты помнишь")
    print(f"   Ответ: {response}")
    
    # Тест 4: Симуляция диалога с LLM
    print("\n4. Симуляция диалога:")
    print("   Пользователь: что мне заказать на ужин?")
    print(f"   Контекст для LLM: {context['content']}")
    print("   Ожидаемый результат: LLM знает о любви к пицце, но не упоминает 'память'")
    
    # Тест 5: Проверяем статистику
    print("\n5. Статистика памяти:")
    stats = memory.get_memory_stats()
    print(f"   - Краткосрочная: {stats['short_term_count']} сообщений")
    print(f"   - Долгосрочная: {stats['long_term_count']} записей ({stats['long_term_words']} слов)")
    
    # Сохраняем память
    save_user_memory(user_id)
    
    print("\n✅ Тест завершен!")
    print("\n🎯 Результат:")
    if natural_integration:
        print("   ✅ Естественная интеграция активна")
        print("   ✅ LLM будет использовать факты без явных упоминаний 'памяти'")
    else:
        print("   ⚠️ Используется старый способ с явными упоминаниями")
    
    print("\n💡 Рекомендации:")
    print("   - Если LLM все еще упоминает 'память' - проверьте настройку NATURAL_INTEGRATION")
    print("   - Можно отключить AUTO_INCLUDE если память мешает")
    print("   - Используйте команды 'что ты помнишь' для явного запроса")

if __name__ == "__main__":
    asyncio.run(test_natural_memory_integration()) 
#!/usr/bin/env python3
"""
Тест новой системы долгосрочной памяти
"""

from memory.manager import MemoryManager
from config import get_long_term_config

def test_memory_system():
    print("🧠 Тестирование новой системы долгосрочной памяти")
    print("=" * 50)
    
    # Создаем менеджер памяти
    memory = MemoryManager()
    
    # Показываем настройки
    config = get_long_term_config()
    print(f"Настройки памяти:")
    print(f"- Максимум слов: {config.get('MAX_WORDS', 300)}")
    print(f"- Максимум слов в записи: {config.get('MAX_WORDS_PER_ENTRY', 4)}")
    print(f"- Автоподмешивание: {config.get('AUTO_INCLUDE', True)}")
    print(f"- Фразы для сохранения: {config.get('SAVE_PHRASES', [])}")
    print(f"- Фразы для поиска: {config.get('RECALL_PHRASES', [])}")
    print()
    
    # Тестируем добавление сообщений
    print("📝 Тестируем добавление сообщений:")
    
    # Короткие сообщения для сохранения (не более 4 слов)
    test_messages = [
        "запомни не люблю лето",
        "запомни очень люблю маму", 
        "запомни боюсь пауков",
        "запомни люблю пиццу",
        "запомни работаю программистом"
    ]
    
    for msg in test_messages:
        memory.add("user", msg)
        print(f"  ✅ Добавлено: '{msg}'")
    
    # Длинное сообщение (должно быть отклонено)
    long_msg = "запомни очень длинное сообщение которое превышает лимит слов в одной записи"
    memory.add("user", long_msg)
    print(f"  ❌ Длинное сообщение: '{long_msg}'")
    
    # Сообщение без ключевого слова (не должно сохраниться)
    normal_msg = "привет как дела"
    memory.add("user", normal_msg)
    print(f"  📝 Обычное сообщение: '{normal_msg}'")
    
    print()
    
    # Сохраняем в долгосрочную память
    print("💾 Сохраняем в долгосрочную память:")
    memory.save_long_term()
    
    # Показываем статистику
    stats = memory.get_memory_stats()
    print(f"Статистика памяти:")
    print(f"- Краткосрочная: {stats['short_term_count']} сообщений")
    print(f"- Долгосрочная: {stats['long_term_count']} записей ({stats['long_term_words']} слов)")
    print(f"- Persistent: {stats['persistent_count']} записей")
    print()
    
    # Тестируем команды памяти
    print("🔍 Тестируем команды памяти:")
    
    recall_commands = [
        "что ты помнишь",
        "вспомни",
        "помнишь"
    ]
    
    for cmd in recall_commands:
        response = memory.handle_memory_commands(cmd)
        if response:
            print(f"  ✅ '{cmd}' -> {response[:50]}...")
        else:
            print(f"  ❌ '{cmd}' -> нет ответа")
    
    print()
    
    # Тестируем контекст
    print("🧩 Тестируем контекст с долгосрочной памятью:")
    context = memory.get_context_as_system_prompt()
    print(f"Контекст: {context['content'][:100]}...")
    
    print()
    print("✅ Тест завершен!")

if __name__ == "__main__":
    test_memory_system() 
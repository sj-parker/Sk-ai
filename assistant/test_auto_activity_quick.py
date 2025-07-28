#!/usr/bin/env python3
"""
Быстрый тест автоматической активности
"""

import asyncio
from auto_activity import AutoActivityManager
from config import is_auto_activity_enabled

async def quick_test():
    """Быстрый тест основных функций"""
    print("🚀 Быстрый тест автоматической активности")
    print("-" * 40)
    
    # Проверяем конфигурацию
    if not is_auto_activity_enabled():
        print("❌ Автоматическая активность отключена в конфигурации")
        print("Включите AUTO_ACTIVITY.ENABLED: true в config.yaml")
        return
    
    print("✅ Автоматическая активность включена")
    
    # Создаем менеджер
    manager = AutoActivityManager()
    
    # Тестируем выбор типа активности
    activity_type = manager.choose_activity_type()
    print(f"🎯 Выбранный тип: {activity_type}")
    
    # Тестируем генерацию промпта
    context = "Тестовый контекст: Привет всем!"
    prompt = manager.generate_activity_prompt(activity_type, context)
    print(f"📝 Промпт (первые 150 символов):")
    print(f"   {prompt[:150]}...")
    
    print("\n✅ Тест завершен успешно!")
    print("\n💡 Для полного тестирования запустите:")
    print("   python test_auto_activity.py")

if __name__ == "__main__":
    asyncio.run(quick_test()) 
#!/usr/bin/env python3
"""
Тест автоматической активности ассистента
"""

import asyncio
import time
from auto_activity import AutoActivityManager, force_activate_auto_activity
from config import is_auto_activity_enabled, get_inactivity_timeout, get_activity_check_interval

def test_auto_activity_config():
    """Тестирует конфигурацию автоматической активности"""
    print("=== Тест конфигурации автоматической активности ===")
    print(f"Автоматическая активность включена: {is_auto_activity_enabled()}")
    print(f"Таймаут неактивности: {get_inactivity_timeout()} секунд")
    print(f"Интервал проверки: {get_activity_check_interval()} секунд")
    print()

def test_activity_manager():
    """Тестирует менеджер автоматической активности"""
    print("=== Тест менеджера автоматической активности ===")
    
    manager = AutoActivityManager()
    
    # Тест обновления времени
    old_time = manager.last_message_time
    time.sleep(1)
    manager.update_last_message_time()
    new_time = manager.last_message_time
    
    print(f"Время обновлено: {old_time != new_time}")
    
    # Тест выбора типа активности
    activity_type = manager.choose_activity_type()
    print(f"Выбранный тип активности: {activity_type}")
    
    # Тест генерации промпта
    context = "Пользователь1: Привет!\nПользователь2: Как дела?"
    prompt = manager.generate_activity_prompt(activity_type, context)
    print(f"Сгенерированный промпт (первые 100 символов): {prompt[:100]}...")
    print()

async def test_force_activation():
    """Тестирует принудительную активацию"""
    print("=== Тест принудительной активации ===")
    
    if not is_auto_activity_enabled():
        print("Автоматическая активность отключена в конфигурации")
        return
    
    print("Запускаем принудительную активацию...")
    force_activate_auto_activity()
    
    # Ждем немного для обработки
    await asyncio.sleep(5)
    print("Принудительная активация завершена")
    print()

async def test_auto_activity_lifecycle():
    """Тестирует полный жизненный цикл автоматической активности"""
    print("=== Тест жизненного цикла автоматической активности ===")
    
    if not is_auto_activity_enabled():
        print("Автоматическая активность отключена в конфигурации")
        return
    
    manager = AutoActivityManager()
    
    print("Запускаем автоматическую активность...")
    manager.start()
    
    # Ждем немного
    await asyncio.sleep(10)
    
    print("Останавливаем автоматическую активность...")
    manager.stop()
    
    print("Тест завершен")
    print()

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование автоматической активности ассистента")
    print("=" * 60)
    
    # Тест конфигурации
    test_auto_activity_config()
    
    # Тест менеджера
    test_activity_manager()
    
    # Запускаем асинхронные тесты
    async def run_async_tests():
        await test_force_activation()
        await test_auto_activity_lifecycle()
    
    try:
        asyncio.run(run_async_tests())
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    main() 
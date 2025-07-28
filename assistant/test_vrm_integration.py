#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции VRM с ассистентом
"""

import asyncio
import json
import websockets
import time
from overlay_server import send_emotion_to_vrm, send_animation_to_vrm

async def test_vrm_integration():
    """Тестирует интеграцию с VRM через WebSocket"""
    
    # Настройки подключения
    ws_host = '192.168.1.4'  # Измените на ваш IP
    ws_port = 31992
    
    try:
        print(f"🔌 Подключение к WebSocket: ws://{ws_host}:{ws_port}")
        
        async with websockets.connect(f"ws://{ws_host}:{ws_port}") as websocket:
            print("✅ Подключение установлено")
            
            # Отправляем идентификатор VRM клиента
            await websocket.send(json.dumps({
                'type': 'vrm_client',
                'client': 'test_vrm',
                'version': '1.0'
            }))
            print("📤 Отправлен идентификатор VRM клиента")
            
            # Тестируем различные команды
            test_commands = [
                {
                    'type': 'status',
                    'status': 'thinking'
                },
                {
                    'type': 'emotion',
                    'emotion': 'happy',
                    'intensity': 1.0,
                    'duration': 2000
                },
                {
                    'type': 'animation',
                    'animation': 'talking',
                    'duration': 3000
                },
                {
                    'type': 'text',
                    'text': 'Привет! Это тестовое сообщение от ассистента.',
                    'duration': 5000
                },
                {
                    'type': 'speech',
                    'isSpeaking': True,
                    'text': 'Тестирую речь...'
                },
                {
                    'type': 'speech',
                    'isSpeaking': False,
                    'text': ''
                },
                {
                    'type': 'status',
                    'status': 'idle'
                }
            ]
            
            for i, command in enumerate(test_commands):
                print(f"\n🧪 Тест {i+1}/{len(test_commands)}: {command['type']}")
                await websocket.send(json.dumps(command))
                
                # Ждем немного между командами
                await asyncio.sleep(2)
            
            print("\n✅ Все тесты завершены")
            
            # Ждем немного для получения ответов
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("Убедитесь, что ассистент запущен и WebSocket сервер активен")

async def test_overlay_commands():
    """Тестирует отправку команд через overlay сервер"""
    
    try:
        # Импортируем функции из overlay_server
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'assistant'))
        
        from overlay_server import (
            send_emotion_to_vrm,
            send_animation_to_vrm,
            send_status_to_vrm,
            send_speech_to_vrm,
            send_text_to_vrm
        )
        
        print("🧪 Тестирование команд через overlay сервер...")
        
        # Тестируем различные команды
        await send_status_to_vrm("thinking")
        print("✅ Отправлен статус 'thinking'")
        
        await asyncio.sleep(1)
        
        await send_emotion_to_vrm("happy", 1.0, 2000)
        print("✅ Отправлена эмоция 'happy'")
        
        await asyncio.sleep(1)
        
        await send_animation_to_vrm("talking", 3000)
        print("✅ Отправлена анимация 'talking'")
        
        await asyncio.sleep(1)
        
        await send_text_to_vrm("Тестовое сообщение от overlay сервера!", 5000)
        print("✅ Отправлен текст")
        
        await asyncio.sleep(1)
        
        await send_speech_to_vrm(True, "Тестирую речь...")
        print("✅ Отправлен статус речи 'началась'")
        
        await asyncio.sleep(2)
        
        await send_speech_to_vrm(False)
        print("✅ Отправлен статус речи 'закончилась'")
        
        await asyncio.sleep(1)
        
        await send_status_to_vrm("idle")
        print("✅ Отправлен статус 'idle'")
        
        print("\n✅ Все команды overlay сервера протестированы")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что вы находитесь в корневой папке проекта")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def test_emotions_and_animations():
    # Тест эмоций
    print("Тест: 😊 (happy)")
    await send_emotion_to_vrm("happy", 1.0, 2000)
    await asyncio.sleep(2.5)

    print("Тест: 😢 (sad)")
    await send_emotion_to_vrm("sad", 1.0, 2000)
    await asyncio.sleep(2.5)

    print("Тест: 😡 (angry)")
    await send_emotion_to_vrm("angry", 1.0, 2000)
    await asyncio.sleep(2.5)

    print("Тест: 😱 (surprised)")
    await send_emotion_to_vrm("surprised", 1.0, 2000)
    await asyncio.sleep(2.5)

    # Тест движений
    print("Тест: greeting")
    await send_animation_to_vrm("greeting", 2000)
    await asyncio.sleep(2.5)

    print("Тест: excitement")
    await send_animation_to_vrm("excitement", 2000)
    await asyncio.sleep(2.5)

    print("Тест: surprise")
    await send_animation_to_vrm("surprise", 2000)
    await asyncio.sleep(2.5)

    print("Тест: thinking")
    await send_animation_to_vrm("thinking", 2000)
    await asyncio.sleep(2.5)

async def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск тестов интеграции VRM с ассистентом")
    print("=" * 50)
    
    # Тест 1: Прямое WebSocket подключение
    print("\n📡 Тест 1: Прямое WebSocket подключение")
    await test_vrm_integration()
    
    print("\n" + "=" * 50)
    
    # Тест 2: Команды через overlay сервер
    print("\n🎮 Тест 2: Команды через overlay сервер")
    await test_overlay_commands()
    
    print("\n" + "=" * 50)
    
    # Тест 3: Тестирование эмоций и анимаций
    print("\n🎭 Тест 3: Тестирование эмоций и анимаций")
    await test_emotions_and_animations()
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main()) 
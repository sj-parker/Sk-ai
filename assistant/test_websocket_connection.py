#!/usr/bin/env python3
"""
Тест WebSocket соединения
"""

import asyncio
import websockets
import socket

async def test_websocket():
    """Тестирует подключение к WebSocket серверу"""
    
    # Настройки подключения
    ws_host = '192.168.1.4'
    ws_port = 31992
    
    try:
        print(f"🔌 Тестирование подключения к ws://{ws_host}:{ws_port}")
        
        # Сначала проверим, доступен ли порт
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ws_host, ws_port))
        sock.close()
        
        if result != 0:
            print(f"❌ Порт {ws_port} недоступен на {ws_host}")
            print("💡 Убедитесь, что WebSocket сервер запущен")
            return False
        
        print(f"✅ Порт {ws_port} доступен")
        
        # Теперь попробуем WebSocket подключение
        async with websockets.connect(f"ws://{ws_host}:{ws_port}") as websocket:
            print("✅ WebSocket соединение установлено!")
            
            # Отправляем тестовое сообщение
            test_message = {
                'type': 'ping',
                'timestamp': asyncio.get_event_loop().time()
            }
            await websocket.send(str(test_message))
            print("📤 Тестовое сообщение отправлено")
            
            # Ждем ответ
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Получен ответ: {response}")
                return True
            except asyncio.TimeoutError:
                print("⏰ Таймаут ожидания ответа")
                return False
                
    except websockets.exceptions.InvalidURI:
        print("❌ Неверный URI WebSocket")
        return False
    except websockets.exceptions.ConnectionClosed:
        print("❌ Соединение закрыто сервером")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    if result:
        print("🎉 WebSocket тест прошел успешно!")
    else:
        print("💥 WebSocket тест не прошел") 
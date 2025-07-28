import asyncio
import websockets
import socket
from monitor import module_status, error_log
import time
import json

connected_clients = set()
text_overlay_clients = set()
vrm_clients = set()  # Новый набор для VRM клиентов
server_ref = None
text_server_ref = None

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"🔌 Новый клиент подключен. Всего клиентов: {len(connected_clients)}")
    try:
        async for message in websocket:
            # Обрабатываем сообщения от клиентов
            try:
                data = json.loads(message)
                print(f"📨 Получено сообщение: {data}")
                if data.get('type') == 'vrm_client':
                    # Это VRM клиент
                    vrm_clients.add(websocket)
                    print(f"🎭 VRM клиент подключен. Всего VRM клиентов: {len(vrm_clients)}")
                    # Отправляем подтверждение
                    await websocket.send(json.dumps({
                        'type': 'client_ack',
                        'client': data.get('client'),
                        'message': 'VRM клиент подтвержден'
                    }))
                elif data.get('type') == 'ping':
                    # Отвечаем на ping
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': data.get('timestamp')
                    }))
                    print(f"🏓 Отправлен pong клиенту")
                elif data.get('type') in ('pose_control', 'camera_control', 'light_control'):
                    # Ретранслируем команды управления VRM-клиентам
                    await send_to_vrm(data)
                else:
                    print(f"❓ Неизвестный тип сообщения: {data.get('type')}")
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}, сообщение: {message}")
                # Обычный overlay клиент
                pass
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Соединение закрыто клиентом")
    except Exception as e:
        print(f"❌ Ошибка в handler: {e}")
    finally:
        connected_clients.remove(websocket)
        vrm_clients.discard(websocket)
        print(f"🔌 Клиент отключен. Осталось клиентов: {len(connected_clients)}")

async def text_handler(websocket):
    print("Text overlay client connected")
    text_overlay_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        print("Text overlay client disconnected")
        text_overlay_clients.remove(websocket)

async def broadcast(message: str):
    # Отправлять только валидный JSON
    try:
        json.loads(message)  # Проверка, что message — валидный JSON
    except Exception:
        print(f"[WARN] Не отправляю не-JSON сообщение: {message}")
        return
    if connected_clients:
        await asyncio.gather(*(ws.send(message) for ws in connected_clients))

async def broadcast_text(message: str):
    print(f"[DEBUG] Broadcasting to {len(text_overlay_clients)} clients: {message!r}")
    if text_overlay_clients:
        await asyncio.gather(*(ws.send(message) for ws in text_overlay_clients))

async def broadcast_to_vrm(message: dict):
    """Отправляет сообщение всем VRM клиентам"""
    if vrm_clients:
        message_str = json.dumps(message)
        await asyncio.gather(*(ws.send(message_str) for ws in vrm_clients))

async def send_to_overlay(message: str):
    await broadcast(message)

async def send_text_to_overlay(message: str):
    await broadcast_text(message)

async def send_to_vrm(message: dict):
    """Отправляет команду в VRM"""
    await broadcast_to_vrm(message)

# Новые функции для управления VRM
async def send_emotion_to_vrm(emotion: str, intensity: float = 1.0, duration: int = 2000):
    """Отправляет команду эмоции в VRM"""
    await send_to_vrm({
        'type': 'emotion',
        'emotion': emotion,
        'intensity': intensity,
        'duration': duration
    })

async def send_animation_to_vrm(animation: str, duration: int = 5000):
    """Отправляет команду анимации в VRM"""
    await send_to_vrm({
        'type': 'animation',
        'animation': animation,
        'duration': duration
    })

async def send_status_to_vrm(status: str):
    """Отправляет статус в VRM"""
    await send_to_vrm({
        'type': 'status',
        'status': status
    })

async def send_speech_to_vrm(is_speaking: bool, text: str = ""):
    """Отправляет информацию о речи в VRM"""
    await send_to_vrm({
        'type': 'speech',
        'isSpeaking': is_speaking,
        'text': text
    })

async def send_text_to_vrm(text: str, duration: int = 5000):
    """Отправляет текст для отображения в VRM"""
    await send_to_vrm({
        'type': 'text',
        'text': text,
        'duration': duration
    })

async def start_overlay_server(port, host='0.0.0.0', text_port=None):
    global server_ref, text_server_ref
    if server_ref is not None:
        print(f"[Overlay] Сервер уже запущен, повторный старт не требуется.")
        return
    try:
        print(f"🖼️ Overlay сервер запущен на ws://{host}:{port}")
        server_ref = await websockets.serve(handler, host, port)
        module_status['overlay'] = True
        if text_port:
            print(f"📝 Text Overlay сервер запущен на ws://{host}:{text_port}")
            text_server_ref = await websockets.serve(text_handler, host, text_port)
            module_status['text_overlay'] = True
        print(f"[DEBUG] WebSocket серверы запущены успешно")
    except Exception as e:
        print(f"[ERROR] Ошибка запуска WebSocket сервера: {e}")
        error_log.append({'error': f'[Overlay Error]: {e}', 'timestamp': time.strftime('%H:%M:%S')})
        module_status['overlay'] = False
        module_status['text_overlay'] = False

async def stop_overlay_server():
    global server_ref, text_server_ref
    if server_ref:
        print("🛑 Завершаем overlay сервер")
        server_ref.close()
        await server_ref.wait_closed()
        server_ref = None
        module_status['overlay'] = False
    if text_server_ref:
        print("🛑 Завершаем text overlay сервер")
        text_server_ref.close()
        await text_server_ref.wait_closed()
        text_server_ref = None
        module_status['text_overlay'] = False

# Запуск сервера при выполнении файла
if __name__ == "__main__":
    import sys
    import os
    
    # Добавляем путь к проекту для импорта модулей
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from config import get
        
        # Получаем настройки из конфига
        ws_port = get('OVERLAY_WS_PORT', 31992)
        ws_host = get('OVERLAY_WS_HOST', 'localhost')
        text_ws_port = get('TEXT_OVERLAY_WS_PORT', 31993)
        
        print(f"🚀 Запуск WebSocket серверов...")
        print(f"📡 Основной сервер: ws://{ws_host}:{ws_port}")
        print(f"📝 Текстовый сервер: ws://{ws_host}:{text_ws_port}")
        
        # Запускаем серверы
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_overlay_server(ws_port, ws_host, text_ws_port))
        
        print("✅ WebSocket серверы запущены успешно!")
        print("🔄 Серверы работают. Нажмите Ctrl+C для остановки.")
        
        # Держим серверы запущенными
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
            loop.run_until_complete(stop_overlay_server())
            loop.close()
            print("✅ Серверы остановлены.")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что config.py находится в корневой папке проекта")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        import traceback
        traceback.print_exc()

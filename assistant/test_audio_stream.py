#!/usr/bin/env python3
"""
Тест аудио стрима
Проверяет работу аудио стрим сервера и отправку тестового аудио
"""

import asyncio
import websockets
import json
import base64
import wave
import io
import time
import threading

async def test_audio_stream():
    """Тестирует аудио стрим сервер"""
    
    # Настройки подключения
    ws_host = '192.168.1.4'  # Измените на ваш IP
    ws_port = 31995
    
    try:
        print(f"🎵 Тестирование аудио стрима на ws://{ws_host}:{ws_port}")
        
        # Подключаемся к WebSocket
        async with websockets.connect(f"ws://{ws_host}:{ws_port}") as websocket:
            print("✅ Подключение к аудио стриму установлено!")
            
            # Отправляем ping
            ping_message = {
                'type': 'ping',
                'timestamp': time.time()
            }
            await websocket.send(json.dumps(ping_message))
            print("📤 Ping отправлен")
            
            # Ждем pong
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get('type') == 'pong':
                    print("📥 Pong получен - сервер работает!")
                else:
                    print(f"📥 Получен неожиданный ответ: {data}")
            except asyncio.TimeoutError:
                print("⏰ Таймаут ожидания pong")
                return False
            
            # Создаем тестовое аудио (синусоида 440 Гц)
            print("🎵 Создаем тестовое аудио...")
            sample_rate = 48000
            duration = 2  # 2 секунды
            frequency = 440  # A4
            
            # Генерируем синусоиду
            import numpy as np
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t)
            
            # Конвертируем в 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Создаем WAV в памяти
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # моно
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            wav_data = wav_buffer.getvalue()
            audio_b64 = base64.b64encode(wav_data).decode('utf-8')
            
            # Отправляем тестовое аудио
            audio_message = {
                'type': 'audio',
                'data': audio_b64,
                'sample_rate': sample_rate,
                'timestamp': time.time()
            }
            
            await websocket.send(json.dumps(audio_message))
            print(f"🎵 Тестовое аудио отправлено ({len(wav_data)} байт)")
            
            # Ждем немного
            await asyncio.sleep(3)
            print("✅ Тест завершен успешно!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

async def test_audio_server_direct():
    """Тестирует аудио сервер напрямую"""
    try:
        from audio_stream_server import audio_server
        
        print("🎵 Запуск аудио сервера...")
        server_task = asyncio.create_task(audio_server.start_server())
        
        # Ждем запуска сервера
        await asyncio.sleep(2)
        
        if audio_server.is_running:
            print("✅ Аудио сервер запущен")
            
            # Создаем тестовое аудио
            import numpy as np
            sample_rate = 48000
            duration = 1
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t)
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Отправляем тестовое аудио
            await audio_server.broadcast_audio(audio_data.tobytes(), sample_rate)
            print("🎵 Тестовое аудио отправлено через сервер")
            
            # Ждем немного
            await asyncio.sleep(2)
            
            # Останавливаем сервер
            await audio_server.stop_server()
            print("🛑 Аудио сервер остановлен")
            
        else:
            print("❌ Аудио сервер не запустился")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования сервера: {e}")

if __name__ == "__main__":
    print("🎵 Тест аудио стрима")
    print("=" * 50)
    
    # Выбираем тест
    test_type = input("Выберите тест (1 - клиент, 2 - сервер): ").strip()
    
    if test_type == "1":
        asyncio.run(test_audio_stream())
    elif test_type == "2":
        asyncio.run(test_audio_server_direct())
    else:
        print("❌ Неверный выбор") 
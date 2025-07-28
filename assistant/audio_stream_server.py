import asyncio
import websockets
import json
import base64
import wave
import io
import threading
import time
from typing import Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioStreamServer:
    def __init__(self, host='0.0.0.0', port=31995):
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.server = None
        self.is_running = False
        
    async def register_client(self, websocket):
        """Регистрирует нового клиента"""
        self.clients.add(websocket)
        logger.info(f"🎵 Аудио клиент подключен. Всего клиентов: {len(self.clients)}")
        
    async def unregister_client(self, websocket):
        """Удаляет клиента"""
        self.clients.discard(websocket)
        logger.info(f"🎵 Аудио клиент отключен. Осталось клиентов: {len(self.clients)}")
        
    async def broadcast_audio(self, audio_data: bytes, sample_rate: int = 48000):
        """Отправляет аудио всем подключенным клиентам"""
        if not self.clients:
            logger.warning("🎵 Нет подключенных аудио клиентов")
            return
            
        try:
            # Создаем WAV файл в памяти
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # моно
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            wav_data = wav_buffer.getvalue()
            audio_b64 = base64.b64encode(wav_data).decode('utf-8')
            
            message = {
                'type': 'audio',
                'data': audio_b64,
                'sample_rate': sample_rate,
                'timestamp': time.time()
            }
            
            # Отправляем всем клиентам
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
            logger.info(f"🎵 Аудио отправлено {len(self.clients)} клиентам ({len(audio_data)} байт)")
            
        except Exception as e:
            logger.error(f"🎵 Ошибка отправки аудио: {e}")
        
    async def handle_client(self, websocket):
        """Обрабатывает подключение клиента"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'ping':
                        await websocket.send(json.dumps({
                            'type': 'pong',
                            'timestamp': data.get('timestamp')
                        }))
                        logger.debug("🎵 Получен ping, отправлен pong")
                except json.JSONDecodeError:
                    logger.warning(f"🎵 Неверный JSON от клиента: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"🎵 Ошибка обработки клиента: {e}")
        finally:
            await self.unregister_client(websocket)
            
    async def start_server(self):
        """Запускает WebSocket сервер"""
        if self.is_running:
            logger.warning("🎵 Аудио сервер уже запущен")
            return
            
        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            self.is_running = True
            logger.info(f"🎵 Аудио стрим сервер запущен на ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"🎵 Ошибка запуска аудио сервера: {e}")
            raise

    async def stop_server(self):
        """Останавливает WebSocket сервер"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logger.info("🎵 Аудио стрим сервер остановлен")

# Глобальный экземпляр сервера
audio_server = AudioStreamServer()

async def start_audio_stream():
    """Запускает аудио стрим сервер"""
    await audio_server.start_server()

def start_audio_stream_thread():
    """Запускает сервер в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_audio_stream())

if __name__ == "__main__":
    # Запуск сервера
    start_audio_stream_thread() 
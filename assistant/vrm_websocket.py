import asyncio
import websockets
import json
from typing import Optional, Set

class VRMWebSocketServer:
    def __init__(self, host: str = 'localhost', port: int = 31990):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, message: dict):
        if not self.clients:
            return
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in self.clients]
        )

    async def start_server(self):
        self.server = await websockets.serve(self.register, self.host, self.port)
        print(f"VRM WebSocket сервер запущен на ws://{self.host}:{self.port}")

    async def stop_server(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

# Глобальный экземпляр сервера
vrm_server: Optional[VRMWebSocketServer] = None

async def init_vrm_server():
    global vrm_server
    if vrm_server is None:
        vrm_server = VRMWebSocketServer()
        await vrm_server.start_server()

async def send_to_vrm(message: dict):
    if vrm_server:
        await vrm_server.broadcast(message)

# Функции для отправки команд липсинка
async def send_lipsync(values: dict):
    """
    Отправляет команду липсинка в VRM overlay
    
    Args:
        values (dict): Значения для каждой гласной (A, I, U, E, O) от 0 до 1
    """
    message = {
        "type": "lipsync",
        **values
    }
    await send_to_vrm(message)

# Простая функция для отправки значения открытия рта
async def send_mouth_open(value: float):
    """
    Отправляет значение открытия рта (0-1)
    """
    await send_lipsync({"A": value}) 
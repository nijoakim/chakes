import uuid

from fastapi import WebSocket

from chakes.backend.models import GameRoom, MoveRequest


class ConnectionManager:
    def __init__(self):
        self._connections: dict[uuid.UUID, list[WebSocket]] = {}

    async def connect(self, game_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(game_id, []).append(ws)

    def disconnect(self, game_id: uuid.UUID, ws: WebSocket) -> None:
        self._connections[game_id].remove(ws)

    async def broadcast(self, game_id: uuid.UUID, data: dict) -> None:
        for ws in list(self._connections.get(game_id, [])):
            try:
                await ws.send_json(data)
            except Exception:
                pass


class GameRoomService:
    _storage: dict[uuid.UUID, GameRoom] = dict()

    def __getitem__(self, key: uuid.UUID):
        return self._storage[key]

    def create(self):
        key = uuid.uuid4()
        self._storage[key] = GameRoom()
        print(f"Created game room: {key}")
        return key

    def list(self):
        return list(self._storage.keys())


class ChakesService:
    def __init__(self, rooms: GameRoomService, connections: ConnectionManager):
        self._rooms = rooms
        self._connections = connections

    async def connect(self, game_id: uuid.UUID, ws: WebSocket) -> None:
        await self._connections.connect(game_id, ws)
        room = self._rooms[game_id]
        color = (
            "white" if len(self._connections._connections[game_id]) == 1 else "black"
        )
        print("Sending game state")
        await ws.send_json({"color": color, "board": room.serialize_board(), "cooldowns": room.serialize_cooldowns()})

    def disconnect(self, game_id: uuid.UUID, ws: WebSocket) -> None:
        self._connections.disconnect(game_id, ws)

    async def move(self, game_id: uuid.UUID, move: MoveRequest) -> None:
        room = self._rooms[game_id]
        room.state.move_piece(move.from_c, 7 - move.from_r, move.to_c, 7 - move.to_r)
        await self._connections.broadcast(game_id, {"board": room.serialize_board(), "cooldowns": room.serialize_cooldowns()})

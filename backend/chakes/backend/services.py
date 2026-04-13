import uuid

from datetime import datetime

from chakes.engine.game_engine import GameState


class GameRoom:
    state: GameState

    # These should be owned by the engine.
    timestamp_start: datetime
    timestamp_end: datetime | None = None

    def __init__(self):
        self.timestamp_start = datetime.now()


class GameRoomService:
    _storage: dict[uuid.UUID, GameRoom] = dict()

    def get(self, key: uuid.UUID):
        return self._storage[key]

    def create(self):
        key = uuid.uuid4()
        room = GameRoom()
        self._storage[key] = room
        return key

    def list(self):
        return list(self._storage.keys())


class ChakesService:
    def hello(self) -> str:
        return "Fake Engine Hello!"

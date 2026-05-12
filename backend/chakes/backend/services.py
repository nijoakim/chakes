import uuid
from dataclasses import dataclass
from datetime import datetime

from fastapi import WebSocket
from pydantic import BaseModel

from chakes.backend.models import (
    ActiveGame,
    GameDef,
    Lobby,
    MoveRequest,
    Pos,
    generate_lobby_name,
)
from chakes.engine.engine import Pos as EnginePos


@dataclass(frozen=True)
class JoinResult:
    color: str
    game: ActiveGame | None


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def accept(self, ws: WebSocket, lobby_name: str) -> None:
        await ws.accept()
        self._connections.setdefault(lobby_name, []).append(ws)

    def disconnect(self, ws: WebSocket, lobby_name: str) -> None:
        self._connections[lobby_name].remove(ws)
        if not self._connections[lobby_name]:
            del self._connections[lobby_name]

    def connection_count(self, lobby_name: str) -> int:
        return len(self._connections.get(lobby_name, []))

    # exclude_none=True: fields set to None are omitted from the wire payload.
    # Required for `winner`: the frontend checks `'winner' in data` to distinguish
    # "no winner yet" (key absent) from "winner decided" (key present, possibly null).
    # model_dump_json encodes once to a JSON string; send_text avoids a second json.dumps per recipient.
    async def send_to(self, ws: WebSocket, msg: BaseModel) -> None:
        await ws.send_text(msg.model_dump_json(exclude_none=True))

    async def broadcast(self, lobby_name: str, msg: BaseModel) -> None:
        payload = msg.model_dump_json(exclude_none=True)
        for ws in list(self._connections.get(lobby_name, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                pass


class LobbyService:
    def __init__(self):
        self._lobbies: dict[str, Lobby] = {}

    def __getitem__(self, name: str) -> Lobby:
        if name not in self._lobbies:
            self.create(name)
        return self._lobbies[name]

    def create(self, name: str | None = None) -> Lobby:
        lobby_name = name or generate_lobby_name()
        lobby = Lobby(lobby_name)
        self._lobbies[lobby_name] = lobby
        print(f"Created lobby: {lobby_name}")
        return lobby

    def list(self) -> list[str]:
        return list(self._lobbies.keys())

    def values(self):
        return self._lobbies.values()

    def get(self, name: str) -> Lobby | None:
        return self._lobbies.get(name)

    def remove(self, name: str) -> None:
        self._lobbies.pop(name, None)


class ChakesService:
    def __init__(self, lobbies: LobbyService):
        self._lobbies = lobbies

    def player_join(self, lobby_name: str, token: str | None = None) -> JoinResult:
        lobby = self._lobbies[lobby_name]
        color = lobby.assign_color(token)
        return JoinResult(color=color, game=lobby.game)

    def create_game(self, lobby_name: str, game_def: GameDef) -> ActiveGame:
        lobby = self._lobbies[lobby_name]
        return lobby.create_game(game_def)

    def get_legal_moves(self, lobby_name: str, game_id: uuid.UUID, pos: Pos) -> list[list[int]]:
        lobby = self._lobbies[lobby_name]
        if not lobby.game or lobby.game.id != game_id:
            raise ValueError("Game not found")
        return lobby.game.get_legal_moves(pos)

    def move(self, lobby_name: str, game_id: uuid.UUID, move: MoveRequest) -> ActiveGame | None:
        lobby = self._lobbies[lobby_name]
        if not lobby.game or lobby.game.id != game_id:
            raise ValueError("Game not found")
        game = lobby.game
        try:
            game.state.move_piece(EnginePos(move.src.x, move.src.y), EnginePos(move.dst.x, move.dst.y), info=move.promotion or '')
        except ValueError:
            return None
        if game.winner is None:
            _, winner = game.snapshot()
            if winner is not None:
                game.winner = "white" if winner.name == "WHITE" else "black"
                game.timestamp_end = datetime.now()
        return game

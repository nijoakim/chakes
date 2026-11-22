import uuid
from collections.abc import ValuesView
from dataclasses import dataclass

from fastapi import WebSocket
from pydantic import BaseModel

from chakes.backend.models import (
    ActiveGame,
    GameDef,
    Lobby,
    MoveRequest,
    Pos,
    generate_lobby_name,
    validate_lobby_name,
)
from chakes.engine.engine import Player, Pos as EnginePos


class LobbyExistsError(Exception):
    """Raised by LobbyService.create when the requested name is already in use."""


class InvalidLobbyNameError(ValueError):
    """Raised by LobbyService.create when the requested name is not acceptable."""


class MoveNotAllowedError(Exception):
    """Raised by ChakesService.move when the mover does not own the piece."""


_COLOR_PLAYERS = {"white": Player.WHITE, "black": Player.BLACK}
_RANDOM_NAME_ATTEMPTS = 50


@dataclass(frozen=True)
class JoinResult:
    color: str
    game: ActiveGame | None


class ConnectionManager:
    def __init__(self) -> None:
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
    def __init__(self) -> None:
        self._lobbies: dict[str, Lobby] = {}

    def __getitem__(self, name: str) -> Lobby:
        """Plain lookup; raises KeyError if missing (never creates)."""
        return self._lobbies[name]

    def create(self, name: str | None = None) -> Lobby:
        """Create a lobby. No name picks a free random one.

        Raises InvalidLobbyNameError for an unacceptable name and
        LobbyExistsError if the name is taken; an existing lobby is never replaced.
        """
        if name:
            if (problem := validate_lobby_name(name)) is not None:
                raise InvalidLobbyNameError(problem)
            if name in self._lobbies:
                raise LobbyExistsError(name)
            lobby_name = name
        else:
            lobby_name = self._free_random_name()
        return self._add(lobby_name)

    def get_or_create(self, name: str) -> Lobby:
        """Return the named lobby, creating it if missing (the WebSocket join path)."""
        lobby = self._lobbies.get(name)
        return lobby if lobby is not None else self._add(name)

    def _add(self, name: str) -> Lobby:
        lobby = Lobby(name)
        self._lobbies[name] = lobby
        print(f"Created lobby: {name}")
        return lobby

    def _free_random_name(self) -> str:
        for _ in range(_RANDOM_NAME_ATTEMPTS):
            candidate = generate_lobby_name()
            if candidate not in self._lobbies:
                return candidate
        base = generate_lobby_name()
        suffix = 2
        while f"{base}-{suffix}" in self._lobbies:
            suffix += 1
        return f"{base}-{suffix}"

    def list(self) -> list[str]:
        return list(self._lobbies.keys())

    def values(self) -> ValuesView[Lobby]:
        return self._lobbies.values()

    def get(self, name: str) -> Lobby | None:
        return self._lobbies.get(name)

    def remove(self, name: str) -> None:
        self._lobbies.pop(name, None)


class ChakesService:
    def __init__(self, lobbies: LobbyService):
        self._lobbies = lobbies

    def player_join(self, lobby_name: str, token: str | None = None) -> JoinResult:
        # Joining over the WebSocket is what brings a directly-opened lobby into existence.
        lobby = self._lobbies.get_or_create(lobby_name)
        color = lobby.assign_color(token)
        return JoinResult(color=color, game=lobby.game)

    def create_game(self, lobby_name: str, game_def: GameDef) -> ActiveGame:
        lobby = self._lobbies[lobby_name]  # KeyError if missing
        return lobby.create_game(game_def)

    def get_game(self, lobby_name: str, game_id: uuid.UUID) -> ActiveGame:
        lobby = self._lobbies.get(lobby_name)
        if lobby is None or not lobby.game or lobby.game.id != game_id:
            raise ValueError("Game not found")
        return lobby.game

    def get_legal_moves(self, lobby_name: str, game_id: uuid.UUID, pos: Pos) -> list[list[int]]:
        return self.get_game(lobby_name, game_id).get_legal_moves(pos)

    def move(self, lobby_name: str, game_id: uuid.UUID, move: MoveRequest, *, color: str) -> ActiveGame | None:
        """Validate and apply a move on behalf of a connection seated as `color`,
        bumping the game version on success.

        Raises ValueError if the game is not found and MoveNotAllowedError if
        `color` does not own the piece on the source square (spectators own
        nothing). Returns None for an illegal move (including an empty source).

        Deliberately does no snapshot / winner detection: that is the caller's
        job (see api._push_legal_moves), so the move path stays cheap.
        """
        game = self.get_game(lobby_name, game_id)
        piece = game.state.piece_at(EnginePos(move.src.x, move.src.y))
        if piece is not None and piece.owner != _COLOR_PLAYERS.get(color):
            raise MoveNotAllowedError(f"{color} may not move {piece.owner.name.lower()}'s piece")
        try:
            game.state.move_piece(EnginePos(move.src.x, move.src.y), EnginePos(move.dst.x, move.dst.y), info=move.promotion or '')
        except ValueError:
            return None
        game.bump_version()
        return game

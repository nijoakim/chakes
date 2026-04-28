import uuid

from fastapi import WebSocket

from chakes.backend.models import (
    ActiveGame,
    GameDef,
    Lobby,
    MoveRequest,
    generate_lobby_name,
)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, lobby_name: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(lobby_name, []).append(ws)

    def disconnect(self, lobby_name: str, ws: WebSocket) -> None:
        self._connections[lobby_name].remove(ws)
        if not self._connections[lobby_name]:
            del self._connections[lobby_name]

    def connection_count(self, lobby_name: str) -> int:
        return len(self._connections.get(lobby_name, []))

    async def broadcast(self, lobby_name: str, data: dict) -> None:
        for ws in list(self._connections.get(lobby_name, [])):
            try:
                await ws.send_json(data)
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

    def get(self, name: str) -> Lobby | None:
        return self._lobbies.get(name)

    def remove(self, name: str) -> None:
        self._lobbies.pop(name, None)


class ChakesService:
    def __init__(self, lobbies: LobbyService, connections: ConnectionManager):
        self._lobbies = lobbies
        self._connections = connections

    def _game_state_msg(self, game: ActiveGame) -> dict:
        msg: dict = {
            "board": game.serialize_board(),
            "cooldowns": game.serialize_cooldowns(),
            "max_cooldowns": game.serialize_max_cooldowns(),
            "game_id": str(game.id),
        }
        winner = game.state.winner()
        if winner:
            msg["winner"] = "white" if winner.name == "WHITE" else "black"
        return msg

    async def connect(self, lobby_name: str, ws: WebSocket, token: str | None = None) -> None:
        await self._connections.connect(lobby_name, ws)
        lobby = self._lobbies[lobby_name]
        color = lobby.assign_color(token)
        msg: dict = {"color": color}
        if lobby.game:
            msg.update(self._game_state_msg(lobby.game))
        await ws.send_json(msg)

    def disconnect(self, lobby_name: str, ws: WebSocket) -> None:
        self._connections.disconnect(lobby_name, ws)
        if self._connections.connection_count(lobby_name) == 0:
            self._lobbies.remove(lobby_name)
            print(f"Destroyed lobby: {lobby_name}")

    async def create_game(self, lobby_name: str, game_def: GameDef) -> ActiveGame:
        lobby = self._lobbies[lobby_name]
        game = lobby.create_game(game_def)
        await self._connections.broadcast(lobby_name, self._game_state_msg(game))
        return game

    def get_legal_moves(self, lobby_name: str, game_id: uuid.UUID, r: int, c: int) -> list[list[int]]:
        lobby = self._lobbies[lobby_name]
        if not lobby.game or lobby.game.id != game_id:
            raise ValueError("Game not found")
        return lobby.game.get_legal_moves(r, c)

    async def move(self, lobby_name: str, game_id: uuid.UUID, move: MoveRequest) -> bool:
        lobby = self._lobbies[lobby_name]
        if not lobby.game or lobby.game.id != game_id:
            raise ValueError("Game not found")
        game = lobby.game
        try:
            game.state.move_piece(move.from_c, 7 - move.from_r, move.to_c, 7 - move.to_r)
        except ValueError:
            return False
        await self._connections.broadcast(lobby_name, self._game_state_msg(game))
        return True

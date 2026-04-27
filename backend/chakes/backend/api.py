import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chakes.backend.models import GameDef, MoveRequest
from chakes.backend.services import ChakesService, ConnectionManager, LobbyService

router = APIRouter(prefix="/api")

lobbies = LobbyService()
connections = ConnectionManager()
chakes = ChakesService(lobbies, connections)


@router.get("/lobby")
def lobby_list():
    return {"lobbies": lobbies.list()}


@router.post("/lobby")
def lobby_create(name: str | None = None):
    lobby = lobbies.create(name)
    return {"lobby": lobby.name}


@router.get("/lobby/{name}")
def lobby_get(name: str):
    lobby = lobbies[name]
    game_id = str(lobby.game.id) if lobby.game else None
    return {"name": lobby.name, "game_id": game_id}


@router.post("/lobby/{name}/game")
async def game_create(name: str, game_def: GameDef | None = None):
    game = await chakes.create_game(name, game_def or GameDef())
    return {"game_id": str(game.id)}


@router.post("/lobby/{name}/game/{game_id}/move")
async def game_move(name: str, game_id: uuid.UUID, move: MoveRequest):
    await chakes.move(name, game_id, move)


@router.websocket("/lobby/{name}/ws")
async def lobby_ws(name: str, ws: WebSocket):
    await chakes.connect(name, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        chakes.disconnect(name, ws)

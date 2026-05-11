import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from chakes.backend.models import GameDef, MoveRequest, Pos, _DEFAULT_PIECE_NAMES, GAME_TYPES
from chakes.engine.engine import piece_defs as engine_piece_defs
from chakes.backend.services import ChakesService, ConnectionManager, LobbyService

router = APIRouter(prefix="/api")

lobbies = LobbyService()
connections = ConnectionManager()
chakes = ChakesService(lobbies, connections)


@router.get("/game-types")
def game_types_list():
    return {
        "game_types": [
            {"id": key, "name": label}
            for key, (label, _) in GAME_TYPES.items()
        ]
    }


@router.get("/piece-defs")
def piece_defs_list():
    return {
        "pieces": [
            {"name": n, "default_cooldown": engine_piece_defs[n][0]}
            for n in _DEFAULT_PIECE_NAMES
        ]
    }


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


@router.get("/lobby/{name}/game/{game_id}/legal-moves")
def game_legal_moves(name: str, game_id: uuid.UUID, r: int, c: int):
    moves = chakes.get_legal_moves(name, game_id, Pos(x=c, y=r))
    return {"moves": moves}


@router.post("/lobby/{name}/game/{game_id}/move")
async def game_move(name: str, game_id: uuid.UUID, move: MoveRequest):
    ok = await chakes.move(name, game_id, move)
    if not ok:
        return JSONResponse(status_code=400, content={"error": "Illegal move"})


@router.websocket("/lobby/{name}/ws")
async def lobby_ws(name: str, ws: WebSocket, token: str | None = None):
    await chakes.connect(name, ws, token)
    try:
        while True:
            text = await ws.receive_text()
            try:
                msg = json.loads(text)
                if msg.get('type') == 'ping':
                    await ws.send_text(json.dumps({'type': 'pong', 'id': msg['id']}))
            except (json.JSONDecodeError, KeyError):
                pass
    except WebSocketDisconnect:
        chakes.disconnect(name, ws)

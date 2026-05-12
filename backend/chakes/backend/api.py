import json
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from chakes.backend.messages import GameStateMessage, LobbyJoinedMessage
from chakes.backend.models import (
    GameDef, MoveRequest, Pos, _DEFAULT_PIECE_NAMES, GAME_TYPES,
    INCOMING_ADAPTER, IncomingMessage, PingMessage, MoveMessage, LegalMovesMessage,
    summarize,
)
from chakes.engine.engine import Pos as EnginePos, piece_defs as engine_piece_defs
from chakes.backend.server_identity import SERVER_NAME
from chakes.backend.services import ChakesService, ConnectionManager, LobbyService

router = APIRouter(prefix="/api")

lobbies = LobbyService()
connections = ConnectionManager()
chakes = ChakesService(lobbies)

print(f"Server name: {SERVER_NAME}")


async def _parse_incoming(ws: WebSocket, raw_text: str) -> IncomingMessage | None:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        await ws.send_json({"type": "error", "error": "invalid_json", "detail": str(e)})
        return None
    try:
        return INCOMING_ADAPTER.validate_python(data)
    except ValidationError as e:
        await ws.send_json({"type": "error", "error": "invalid_message", "detail": e.errors(include_url=False)})
        return None


@router.get("/server")
def server_info() -> dict[str, str]:
    return {"name": SERVER_NAME}


@router.get("/game-types")
def game_types_list() -> dict[str, Any]:
    return {
        "game_types": [
            {"id": key, "name": label}
            for key, (label, _) in GAME_TYPES.items()
        ]
    }


@router.get("/piece-defs")
def piece_defs_list(game_type: str | None = None) -> dict[str, Any]:
    if game_type and game_type in GAME_TYPES:
        factory = GAME_TYPES[game_type][1]
        state = factory()
        seen: set[str] = set()
        names: list[str] = []
        for piece in state.all_pieces():
            if piece.name not in seen:
                seen.add(piece.name)
                names.append(piece.name)
    else:
        names = _DEFAULT_PIECE_NAMES
    return {
        "pieces": [
            {"name": n, "default_cooldown": engine_piece_defs[n][0]}
            for n in names
        ]
    }


@router.get("/initial-board")
def initial_board(game_type: str | None = None) -> dict[str, Any]:
    factory = GAME_TYPES.get(game_type or "orthodox", GAME_TYPES["orthodox"])[1]
    state = factory()
    board = [
        [
            {"name": p.name, "owner": "white" if p.owner.name == "WHITE" else "black"}
            if (p := state.piece_at(EnginePos(c, r))) else None
            for c in range(state.size_x)
        ]
        for r in range(state.size_y)
    ]
    return {"board": board, "size_x": state.size_x, "size_y": state.size_y}


@router.get("/lobby")
def lobby_list() -> dict[str, Any]:
    return {
        "server_name": SERVER_NAME,
        "lobbies": [summarize(lob, connections, SERVER_NAME) for lob in lobbies.values()],
    }


@router.post("/lobby")
def lobby_create(name: str | None = None) -> dict[str, str]:
    lobby = lobbies.create(name)
    return {"lobby": lobby.name}


@router.get("/lobby/{name}")
def lobby_get(name: str) -> dict[str, str | None]:
    lobby = lobbies[name]
    game_id = str(lobby.game.id) if lobby.game else None
    return {"name": lobby.name, "game_id": game_id}


@router.post("/lobby/{name}/game")
async def game_create(name: str, game_def: GameDef | None = None) -> dict[str, str]:
    game = chakes.create_game(name, game_def or GameDef())
    await connections.broadcast(name, GameStateMessage.from_active_game(game))
    return {"game_id": str(game.id)}


@router.get("/lobby/{name}/game/{game_id}/legal-moves")
def game_legal_moves(name: str, game_id: uuid.UUID, r: int, c: int) -> dict[str, Any]:
    moves = chakes.get_legal_moves(name, game_id, Pos(x=c, y=r))
    return {"moves": moves}


@router.post("/lobby/{name}/game/{game_id}/move")
async def game_move(name: str, game_id: uuid.UUID, move: MoveRequest) -> JSONResponse:
    game = chakes.move(name, game_id, move)
    if game is None:
        return JSONResponse(status_code=400, content={"error": "Illegal move"})
    await connections.broadcast(name, GameStateMessage.from_active_game(game))
    return JSONResponse(status_code=200, content={"status": "OK"})


async def _handle_ping(ws: WebSocket, msg: PingMessage) -> None:
    await ws.send_json({"type": "pong", "id": msg.id})


async def _handle_move(ws: WebSocket, lobby: str, msg: MoveMessage) -> None:
    move = MoveRequest(src=msg.src, dst=msg.dst, promotion=msg.promotion)
    client_move_id = msg.client_move_id
    try:
        game = chakes.move(lobby, msg.game_id, move)
    except ValueError:
        await ws.send_json({"type": "move_result", "ok": False, "error": "game_not_found", "game_id": str(msg.game_id), "client_move_id": client_move_id})
        return
    if game is None:
        await ws.send_json({"type": "move_result", "ok": False, "error": "illegal_move", "client_move_id": client_move_id})
    else:
        await ws.send_json({"type": "move_result", "ok": True, "client_move_id": client_move_id})
        await connections.broadcast(lobby, GameStateMessage.from_active_game(game, include_immutables=False))


async def _handle_legal_moves(ws: WebSocket, lobby: str, msg: LegalMovesMessage) -> None:
    try:
        moves = chakes.get_legal_moves(lobby, msg.game_id, msg.pos)
    except ValueError:
        await ws.send_json({"type": "legal_moves", "error": "game_not_found", "game_id": str(msg.game_id)})
        return
    await ws.send_json({"type": "legal_moves", "pos": msg.pos.model_dump(), "moves": moves})


@router.websocket("/lobby/{name}/ws")
async def lobby_ws(name: str, ws: WebSocket, token: str | None = None) -> None:
    await connections.accept(ws, name)
    join = chakes.player_join(name, token)
    await connections.send_to(ws, LobbyJoinedMessage(color=join.color))
    if join.game is not None:
        await connections.send_to(ws, GameStateMessage.from_active_game(join.game))
    try:
        while True:
            msg = await _parse_incoming(ws, await ws.receive_text())
            if msg is None:
                continue
            match msg:
                case PingMessage():
                    await _handle_ping(ws, msg)
                case MoveMessage():
                    await _handle_move(ws, name, msg)
                case LegalMovesMessage():
                    await _handle_legal_moves(ws, name, msg)
    except WebSocketDisconnect:
        connections.disconnect(ws, name)
        if connections.connection_count(name) == 0:
            lobbies.remove(name)
            print(f"Destroyed lobby: {name}")

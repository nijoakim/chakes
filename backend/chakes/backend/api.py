import asyncio
import json
import logging
import uuid
from collections.abc import Coroutine
from copy import deepcopy
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from chakes.backend.messages import AllLegalMovesMessage, GameStateMessage, LobbyJoinedMessage
from chakes.backend.models import (
    ActiveGame, GameDef, MoveRequest, Pos, _DEFAULT_PIECE_NAMES, GAME_TYPES,
    INCOMING_ADAPTER, IncomingMessage, PingMessage, MoveMessage, LegalMovesMessage,
    compute_snapshot, serialize_legal_moves, summarize,
)
from chakes.engine.engine import Pos as EnginePos, piece_defs as engine_piece_defs
from chakes.backend.server_identity import SERVER_NAME
from chakes.backend.services import (
    ChakesService, ConnectionManager, InvalidLobbyNameError, LobbyExistsError, LobbyService,
    MoveNotAllowedError,
)
from chakes.backend.catalog import game_types_payload, piece_guide

router = APIRouter(prefix="/api")

lobbies = LobbyService()
connections = ConnectionManager()
chakes = ChakesService(lobbies)

logger = logging.getLogger(__name__)

print(f"Server name: {SERVER_NAME}")

# Strong references to in-flight background tasks: the event loop only keeps
# weak ones, so an unreferenced task can be garbage-collected mid-flight.
_background_tasks: set[asyncio.Task[None]] = set()


def _spawn(coro: Coroutine[Any, Any, None]) -> asyncio.Task[None]:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


async def drain_background_tasks() -> None:
    """Await all in-flight background tasks. For tests."""
    while _background_tasks:
        await asyncio.gather(*_background_tasks, return_exceptions=True)


async def _push_legal_moves(lobby_name: str, game: ActiveGame) -> None:
    """Compute all legal moves off the event loop and broadcast them if still current.

    Runs on a deep copy of the board taken on the event loop, so moves applied
    meanwhile cannot race the computation. A winner found is always latched
    (even if the result is otherwise stale); the legal moves are only
    broadcast if no newer move has been applied and the lobby still runs
    this game.
    """
    try:
        version = game.version
        board = deepcopy(game.state)
        all_moves, winner = await asyncio.to_thread(compute_snapshot, board)
        newly_latched = game.record_winner(winner)
        lobby = lobbies.get(lobby_name)
        if lobby is None or lobby.game is not game:
            return
        if game.version != version:
            # Stale moves are dropped, but a winner only this task found must
            # still reach clients: a newer task may already have broadcast
            # without it. Empty legal_moves + stale version: clients apply the
            # winner and ignore the (absent) moves.
            if newly_latched:
                await connections.broadcast(lobby_name, AllLegalMovesMessage(
                    legal_moves={}, game_id=str(game.id), version=version, winner=game.winner,
                ))
            return
        await connections.broadcast(lobby_name, AllLegalMovesMessage(
            legal_moves=serialize_legal_moves(all_moves),
            game_id=str(game.id),
            version=version,
            winner=game.winner,
        ))
    except Exception:
        logger.exception("Legal-moves push failed for lobby %r, game %s", lobby_name, game.id)


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
    return game_types_payload(GAME_TYPES)


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
    try:
        lobby = lobbies.create(name)
    except InvalidLobbyNameError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except LobbyExistsError as e:
        raise HTTPException(status_code=409, detail=f"A lobby named {name!r} already exists.") from e
    return {"lobby": lobby.name}


def _lobby_not_found(name: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"No lobby named {name!r}.")


@router.get("/lobby/{name}")
def lobby_get(name: str) -> dict[str, str | None]:
    lobby = lobbies.get(name)
    if lobby is None:
        raise _lobby_not_found(name)
    game_id = str(lobby.game.id) if lobby.game else None
    return {"name": lobby.name, "game_id": game_id}


@router.post("/lobby/{name}/game")
async def game_create(name: str, game_def: GameDef | None = None) -> dict[str, str]:
    try:
        game = chakes.create_game(name, game_def or GameDef())
    except KeyError as e:
        raise _lobby_not_found(name) from e
    await connections.broadcast(name, GameStateMessage.from_active_game(game))
    return {"game_id": str(game.id)}


@router.get("/lobby/{name}/game/{game_id}/legal-moves")
def game_legal_moves(name: str, game_id: uuid.UUID, r: int, c: int) -> dict[str, Any]:
    try:
        game = chakes.get_game(name, game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Game not found.") from e
    return {"version": game.version, "moves": game.get_legal_moves(Pos(x=c, y=r))}


# Moves are only accepted over the lobby WebSocket, where the sender's seat
# (colour) is known. There is deliberately no REST move endpoint.


async def _handle_ping(ws: WebSocket, msg: PingMessage) -> None:
    await ws.send_json({"type": "pong", "id": msg.id})


async def _handle_move(ws: WebSocket, lobby: str, color: str, msg: MoveMessage) -> None:
    move = MoveRequest(src=msg.src, dst=msg.dst, promotion=msg.promotion)
    client_move_id = msg.client_move_id
    try:
        game = chakes.move(lobby, msg.game_id, move, color=color)
    except MoveNotAllowedError:
        await ws.send_json({"type": "move_result", "ok": False, "error": "not_your_piece", "client_move_id": client_move_id})
        return
    except ValueError:
        await ws.send_json({"type": "move_result", "ok": False, "error": "game_not_found", "game_id": str(msg.game_id), "client_move_id": client_move_id})
        return
    if game is None:
        await ws.send_json({"type": "move_result", "ok": False, "error": "illegal_move", "client_move_id": client_move_id})
    else:
        await ws.send_json({"type": "move_result", "ok": True, "client_move_id": client_move_id})
        await connections.broadcast(lobby, GameStateMessage.from_active_game(game, include_immutables=False, include_legal_moves=False))
        # Legal moves + winner detection are slow; compute them in the
        # background so this socket's receive loop is free right away.
        _spawn(_push_legal_moves(lobby, game))


async def _handle_legal_moves(ws: WebSocket, lobby: str, msg: LegalMovesMessage) -> None:
    try:
        game = chakes.get_game(lobby, msg.game_id)
    except ValueError:
        await ws.send_json({"type": "legal_moves", "error": "game_not_found", "game_id": str(msg.game_id)})
        return
    # Cheap: only this one piece's legal moves, on the current board.
    moves = game.get_legal_moves(msg.pos)
    await ws.send_json({
        "type": "legal_moves", "game_id": str(game.id), "version": game.version,
        "pos": msg.pos.model_dump(), "moves": moves,
    })


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
                    await _handle_move(ws, name, join.color, msg)
                case LegalMovesMessage():
                    await _handle_legal_moves(ws, name, msg)
    except WebSocketDisconnect:
        connections.disconnect(ws, name)
        if connections.connection_count(name) == 0:
            lobbies.remove(name)
            print(f"Destroyed lobby: {name}")


# --- Game-setup catalogue (read-only) ---


def _game_type_piece_names(game_type: str | None) -> list[str]:
    if game_type and game_type in GAME_TYPES:
        state = GAME_TYPES[game_type][1]()
        return sorted({piece.name for piece in state.all_pieces()})
    return list(_DEFAULT_PIECE_NAMES)


@router.get("/piece-guide")
def piece_guide_list(game_type: str | None = None) -> dict[str, Any]:
    """Movement diagrams and rule notes for each piece of a game type."""
    return piece_guide(_game_type_piece_names(game_type))


@router.get("/setup-preview")
def setup_preview(game_type: str | None = None, upside_down: bool = False) -> dict[str, Any]:
    """Starting position as the game will be created, including the upside-down option."""
    state = GAME_TYPES.get(game_type or "orthodox", GAME_TYPES["orthodox"])[1]()
    if upside_down:
        state.upside_down()
    board = [
        [
            {"name": p.name, "owner": "white" if p.owner.name == "WHITE" else "black"}
            if (p := state.piece_at(EnginePos(c, r)))
            else None
            for c in range(state.size_x)
        ]
        for r in range(state.size_y)
    ]
    return {"board": board, "size_x": state.size_x, "size_y": state.size_y}

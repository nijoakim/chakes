"""Move → board broadcast → background legal-moves push (versioned)."""

import json
import logging
import threading
import uuid
from typing import Any, cast

from fastapi import WebSocket

import chakes.backend.api as api
from chakes.backend.models import ActiveGame, GameDef, MoveMessage, Pos, compute_snapshot
from chakes.engine.engine import Player


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _RecordingWS:
    """Stands in for both the mover's socket (send_json) and broadcast targets (send_text)."""

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, data: dict[str, Any]) -> None:
        self.sent.append(data)

    async def send_text(self, payload: str) -> None:
        self.sent.append(json.loads(payload))


def _setup_lobby(name: str = "room") -> tuple[_RecordingWS, ActiveGame]:
    lobby = api.lobbies.create(name)
    game = api.chakes.create_game(name, GameDef())
    ws = _RecordingWS()
    api.connections._connections[name] = cast(list[WebSocket], [ws])
    assert lobby.game is game
    return ws, game


def _move_msg(game_id: uuid.UUID, src: tuple[int, int], dst: tuple[int, int]) -> MoveMessage:
    return MoveMessage(
        type="move", game_id=game_id,
        src=Pos(x=src[0], y=src[1]), dst=Pos(x=dst[0], y=dst[1]),
        client_move_id="cm",
    )


def _ws_move(ws, game_id: str, src: tuple[int, int], dst: tuple[int, int]) -> None:
    ws.send_json({
        "type": "move", "game_id": game_id,
        "src": {"x": src[0], "y": src[1]}, "dst": {"x": dst[0], "y": dst[1]},
        "client_move_id": f"{src}-{dst}",
    })


def _join(ws_connect, lobby_name: str):
    ws = ws_connect(lobby_name, token="tok-white")
    assert ws.receive_json() == {"color": "white"}
    state = ws.receive_json()
    return ws, state


# Fool's mate: f2→f3, e7→e5, g2→g4, d8→h4#
_FOOLS_MATE = [((5, 1), (5, 2)), ((4, 6), (4, 4)), ((6, 1), (6, 3)), ((3, 7), (7, 3))]


# ---------------------------------------------------------------------------
# Over a real WebSocket (TestClient). receive_json() blocks until the next
# message, so no sleeping is needed: each step reads exactly what it expects.
# ---------------------------------------------------------------------------

def test_join_state_includes_version_and_legal_moves(ws_connect, lobby_with_game):
    name, game_id = lobby_with_game
    _, state = _join(ws_connect, name)
    assert state["game_id"] == game_id
    assert state["version"] == 0
    assert "4,1" in state["legal_moves"]


def test_move_sends_result_then_board_then_versioned_legal_moves(ws_connect, lobby_with_game):
    name, game_id = lobby_with_game
    ws, _ = _join(ws_connect, name)

    _ws_move(ws, game_id, (4, 1), (4, 3))

    result = ws.receive_json()
    assert result["type"] == "move_result" and result["ok"] is True

    board = ws.receive_json()
    assert "board" in board
    assert board["version"] == 1
    assert "legal_moves" not in board
    assert "winner" not in board

    push = ws.receive_json()
    assert "board" not in push
    assert push["version"] == 1
    assert push["game_id"] == game_id
    assert "winner" not in push  # exclude_none
    assert "4,3" in push["legal_moves"]
    assert "4,1" not in push["legal_moves"]


def test_per_square_legal_moves_reply_includes_version(ws_connect, lobby_with_game):
    name, game_id = lobby_with_game
    ws, _ = _join(ws_connect, name)

    ws.send_json({"type": "legal_moves", "game_id": game_id, "pos": {"x": 4, "y": 1}})
    reply = ws.receive_json()
    assert reply["type"] == "legal_moves"
    assert reply["version"] == 0
    assert reply["game_id"] == game_id
    assert reply["pos"] == {"x": 4, "y": 1}
    assert sorted(reply["moves"]) == [[4, 2], [4, 3]]

    _ws_move(ws, game_id, (4, 1), (4, 3))
    for _ in range(3):  # move_result, board, legal-moves push
        ws.receive_json()

    ws.send_json({"type": "legal_moves", "game_id": game_id, "pos": {"x": 4, "y": 3}})
    reply = ws.receive_json()
    assert reply["version"] == 1
    assert reply["moves"] == [[4, 4]]


def test_checkmate_winner_arrives_on_legal_moves_push(client, ws_connect, lobby_with_game):
    name, game_id = lobby_with_game
    ws, _ = _join(ws_connect, name)

    for i, (src, dst) in enumerate(_FOOLS_MATE, start=1):
        _ws_move(ws, game_id, src, dst)
        assert ws.receive_json()["ok"] is True
        board = ws.receive_json()
        push = ws.receive_json()
        assert board["version"] == push["version"] == i

    assert "winner" not in board  # board is broadcast before winner detection
    assert push["winner"] == "black"

    entry = next(e for e in client.get("/api/lobby").json()["lobbies"] if e["name"] == name)
    assert entry["state"] == "ended"


def test_rest_move_broadcasts_single_state_with_version_and_legal_moves(client, ws_connect, lobby_with_game):
    name, game_id = lobby_with_game
    ws, _ = _join(ws_connect, name)

    r = client.post(f"/api/lobby/{name}/game/{game_id}/move", json={"src": {"x": 4, "y": 1}, "dst": {"x": 4, "y": 3}})
    assert r.status_code == 200

    state = ws.receive_json()
    assert state["version"] == 1
    assert "4,3" in state["legal_moves"]

    r = client.get(f"/api/lobby/{name}/game/{game_id}/legal-moves", params={"r": 3, "c": 4})
    assert r.json() == {"version": 1, "moves": [[4, 4]]}


def test_rest_move_computes_snapshot_once(client, lobby_with_game, monkeypatch):
    name, game_id = lobby_with_game
    game = api.lobbies[name].game
    assert game is not None
    calls = 0
    real = game.snapshot

    def counting():
        nonlocal calls
        calls += 1
        return real()

    monkeypatch.setattr(game, "snapshot", counting)
    client.post(f"/api/lobby/{name}/game/{game_id}/move", json={"src": {"x": 4, "y": 1}, "dst": {"x": 4, "y": 3}})
    assert calls == 1


# ---------------------------------------------------------------------------
# Background task, driven directly (deterministic: tasks are awaited)
# ---------------------------------------------------------------------------

async def test_handle_move_returns_before_snapshot_finishes(monkeypatch):
    ws, game = _setup_lobby()
    release = threading.Event()

    def gated(board):
        release.wait(timeout=5)
        return compute_snapshot(board)

    monkeypatch.setattr(api, "compute_snapshot", gated)

    await api._handle_move(cast(WebSocket, ws), "room", _move_msg(game.id, (4, 1), (4, 3)))

    # Handler returned with the snapshot still blocked: result + board only.
    assert [m.get("type") for m in ws.sent] == ["move_result", None]
    assert "board" in ws.sent[1]
    assert len(api._background_tasks) == 1

    release.set()
    await api.drain_background_tasks()
    assert not api._background_tasks
    assert ws.sent[2]["version"] == 1
    assert "legal_moves" in ws.sent[2]


async def test_superseded_snapshot_is_dropped_but_winner_latched(monkeypatch):
    ws, game = _setup_lobby()

    def superseded(board):
        moves, _ = compute_snapshot(board)
        game.version += 1  # a newer move landed while we were computing
        return moves, Player.WHITE

    monkeypatch.setattr(api, "compute_snapshot", superseded)
    await api._push_legal_moves("room", game)

    assert ws.sent == []
    assert game.winner == "white"
    assert game.timestamp_end is not None


async def test_snapshot_dropped_when_lobby_has_new_game(monkeypatch):
    ws, game = _setup_lobby()

    def replaced(board):
        api.chakes.create_game("room", GameDef())
        return compute_snapshot(board)

    monkeypatch.setattr(api, "compute_snapshot", replaced)
    await api._push_legal_moves("room", game)
    assert ws.sent == []


async def test_snapshot_dropped_when_lobby_removed(monkeypatch):
    ws, game = _setup_lobby()

    def removed(board):
        api.lobbies.remove("room")
        return compute_snapshot(board)

    monkeypatch.setattr(api, "compute_snapshot", removed)
    await api._push_legal_moves("room", game)
    assert ws.sent == []


async def test_snapshot_runs_on_a_copy_of_the_board(monkeypatch):
    _, game = _setup_lobby()
    seen = []

    def spy(board):
        seen.append(board)
        return compute_snapshot(board)

    monkeypatch.setattr(api, "compute_snapshot", spy)
    await api._push_legal_moves("room", game)
    assert seen and seen[0] is not game.state


async def test_current_snapshot_is_broadcast_with_version_and_winner(monkeypatch):
    ws, game = _setup_lobby()
    game.version = 7
    monkeypatch.setattr(api, "compute_snapshot", lambda board: (compute_snapshot(board)[0], Player.BLACK))
    await api._push_legal_moves("room", game)
    assert len(ws.sent) == 1
    assert ws.sent[0]["version"] == 7
    assert ws.sent[0]["winner"] == "black"
    assert "4,1" in ws.sent[0]["legal_moves"]


async def test_background_task_exception_is_logged(monkeypatch, caplog):
    ws, game = _setup_lobby()

    def broken(board):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(api, "compute_snapshot", broken)
    with caplog.at_level(logging.ERROR, logger="chakes.backend.api"):
        await api._handle_move(cast(WebSocket, ws), "room", _move_msg(game.id, (4, 1), (4, 3)))
        await api.drain_background_tasks()

    errors = [r for r in caplog.records if r.levelno == logging.ERROR and r.exc_info]
    assert len(errors) == 1
    assert isinstance(errors[0].exc_info[1], RuntimeError)
    assert len(ws.sent) == 2  # move_result + board, no push

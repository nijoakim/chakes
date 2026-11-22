from typing import Any

import pytest
from fastapi.testclient import TestClient

import chakes.backend.api as api
from chakes.backend.app import app


@pytest.fixture(autouse=True)
def reset_singletons():
    api.lobbies._lobbies.clear()
    api.connections._connections.clear()
    yield
    api.lobbies._lobbies.clear()
    api.connections._connections.clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def lobby_with_game(client):
    r = client.post("/api/lobby", params={"name": "test-lobby"})
    name = r.json()["lobby"]
    r = client.post(f"/api/lobby/{name}/game")
    game_id = r.json()["game_id"]
    return name, game_id


@pytest.fixture()
def ws_connect(client):
    """Open one or more WS connections to a lobby and clean them up on teardown."""
    opened = []

    def _open(lobby_name: str, token: str | None = None):
        url = f"/api/lobby/{lobby_name}/ws" + (f"?token={token}" if token else "")
        ctx = client.websocket_connect(url)
        ws = ctx.__enter__()
        opened.append((ctx, ws))
        return ws

    yield _open
    for ctx, _ in opened:
        ctx.__exit__(None, None, None)



def _ws_move(ws: Any, game_id: str, src: tuple[int, int], dst: tuple[int, int]) -> dict[str, Any]:
    ws.send_json({
        "type": "move",
        "game_id": game_id,
        "src": {"x": src[0], "y": src[1]},
        "dst": {"x": dst[0], "y": dst[1]},
    })
    # Skip state broadcasts (they carry no "type") until our reply arrives.
    while True:
        msg: dict[str, Any] = ws.receive_json()
        if msg.get("type") == "move_result":
            return msg


@pytest.fixture()
def ws_move():
    """`ws_move(ws, game_id, (x, y), (x, y))` sends a move and returns the move_result reply."""
    return _ws_move


@pytest.fixture()
def seated(ws_connect):
    """Connect a white and a black player (by token) to a lobby, draining the join messages."""
    def _seat(lobby_name: str):
        white = ws_connect(lobby_name, token="tok-white")
        assert white.receive_json() == {"color": "white"}
        black = ws_connect(lobby_name, token="tok-black")
        assert black.receive_json() == {"color": "black"}
        return white, black
    return _seat

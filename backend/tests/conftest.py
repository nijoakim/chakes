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

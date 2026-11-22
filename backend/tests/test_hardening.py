"""Server-side authorisation and lobby lifecycle guarantees."""

from typing import Any

import pytest

import chakes.backend.api as api
import chakes.backend.services as services
from chakes.backend.models import GameDef, MoveRequest, Pos
from chakes.backend.services import ChakesService, LobbyService, MoveNotAllowedError
from chakes.engine.engine import Pos as EnginePos


E2, E4 = (4, 1), (4, 3)
E7, E5 = (4, 6), (4, 4)


def _start_game(client: Any, name: str) -> str:
    game_id: str = client.post(f"/api/lobby/{name}/game").json()["game_id"]
    return game_id


def _piece_at(name: str, xy: tuple[int, int]):
    lobby = api.lobbies.get(name)
    assert lobby is not None and lobby.game is not None
    return lobby.game.state.piece_at(EnginePos(*xy))


# ---------------------------------------------------------------------------
# Move authorisation (WebSocket)
# ---------------------------------------------------------------------------

def test_ws_spectator_move_is_rejected(client, ws_connect, seated, ws_move):
    client.post("/api/lobby", params={"name": "auth"})
    white, black = seated("auth")
    spectator = ws_connect("auth", token="tok-spectator")
    assert spectator.receive_json() == {"color": "spectator"}
    game_id = _start_game(client, "auth")

    result = ws_move(spectator, game_id, E2, E4)

    assert result["ok"] is False
    assert result["error"] == "not_your_piece"
    assert _piece_at("auth", E2) is not None
    assert _piece_at("auth", E4) is None


def test_ws_player_moving_opponents_piece_is_rejected(client, seated, ws_move):
    client.post("/api/lobby", params={"name": "auth"})
    white, black = seated("auth")
    game_id = _start_game(client, "auth")

    assert ws_move(white, game_id, E7, E5)["error"] == "not_your_piece"
    assert ws_move(black, game_id, E2, E4)["error"] == "not_your_piece"
    assert _piece_at("auth", E7) is not None
    assert _piece_at("auth", E2) is not None


def test_ws_players_moving_own_pieces_are_accepted(client, seated, ws_move):
    client.post("/api/lobby", params={"name": "auth"})
    white, black = seated("auth")
    game_id = _start_game(client, "auth")

    assert ws_move(white, game_id, E2, E4)["ok"] is True
    assert ws_move(black, game_id, E7, E5)["ok"] is True
    assert _piece_at("auth", E4) is not None
    assert _piece_at("auth", E5) is not None


def test_ws_illegal_own_move_still_reports_illegal_move(client, seated, ws_move):
    client.post("/api/lobby", params={"name": "auth"})
    white, _ = seated("auth")
    game_id = _start_game(client, "auth")

    result = ws_move(white, game_id, E2, (4, 4))
    assert result["ok"] is False
    assert result["error"] == "illegal_move"


def test_ws_tokenless_join_cannot_take_a_free_seat(client, ws_connect, ws_move):
    client.post("/api/lobby", params={"name": "anon"})
    white = ws_connect("anon", token="tok-white")
    assert white.receive_json() == {"color": "white"}
    anon = ws_connect("anon")
    assert anon.receive_json() == {"color": "spectator"}
    game_id = _start_game(client, "anon")

    assert ws_move(anon, game_id, E7, E5)["error"] == "not_your_piece"
    # The black seat is still free for a real (tokened) player.
    black = ws_connect("anon", token="tok-black")
    assert black.receive_json() == {"color": "black"}


def test_ws_rejoin_with_same_token_keeps_seat_and_can_move(client, ws_connect, ws_move):
    client.post("/api/lobby", params={"name": "rejoin"})
    ws_connect("rejoin", token="tok-white").receive_json()
    ws_connect("rejoin", token="tok-black").receive_json()
    game_id = _start_game(client, "rejoin")

    again = ws_connect("rejoin", token="tok-white")
    assert again.receive_json() == {"color": "white"}
    again.receive_json()  # initial game state
    assert ws_move(again, game_id, E2, E4)["ok"] is True


# ---------------------------------------------------------------------------
# Move authorisation (service)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("color", ["spectator", "black"])
def test_service_move_rejects_non_owner(color):
    lobbies = LobbyService()
    svc = ChakesService(lobbies)
    lobbies.create("svc")
    game = svc.create_game("svc", GameDef())
    with pytest.raises(MoveNotAllowedError):
        svc.move("svc", game.id, MoveRequest(src=Pos(x=4, y=1), dst=Pos(x=4, y=3)), color=color)
    assert game.state.piece_at(EnginePos(4, 1)) is not None


def test_rest_move_endpoint_is_gone(client, lobby_with_game):
    name, game_id = lobby_with_game
    r = client.post(
        f"/api/lobby/{name}/game/{game_id}/move",
        json={"src": {"x": 4, "y": 1}, "dst": {"x": 4, "y": 3}},
    )
    assert r.status_code in (404, 405)
    assert _piece_at(name, E2) is not None


# ---------------------------------------------------------------------------
# Lobby creation
# ---------------------------------------------------------------------------

def test_create_duplicate_name_returns_409_and_keeps_original(client, lobby_with_game):
    name, game_id = lobby_with_game
    original = api.lobbies.get(name)

    r = client.post("/api/lobby", params={"name": name})

    assert r.status_code == 409
    assert name in r.json()["detail"]
    assert api.lobbies.get(name) is original
    assert client.get(f"/api/lobby/{name}").json()["game_id"] == game_id


@pytest.mark.parametrize("bad", [
    "x" * 41,
    "a/b",
    "<script>",
    "semi;colon",
    "   ",
    " padded",
    "tab\there",
])
def test_create_invalid_name_is_rejected(client, bad):
    r = client.post("/api/lobby", params={"name": bad})
    assert r.status_code == 422
    assert client.get("/api/lobby").json()["lobbies"] == []


@pytest.mark.parametrize("good", ["x" * 40, "My lobby 2", "a_b-c.d", "Ålesund", "日本"])
def test_create_valid_name_is_accepted(client, good):
    r = client.post("/api/lobby", params={"name": good})
    assert r.status_code == 200
    assert r.json()["lobby"] == good


def test_create_random_name_avoids_existing_lobbies(client, monkeypatch):
    names = iter(["taken-name", "taken-name", "fresh-name"])
    monkeypatch.setattr(services, "generate_lobby_name", lambda: next(names))
    assert client.post("/api/lobby").json()["lobby"] == "taken-name"
    assert client.post("/api/lobby").json()["lobby"] == "fresh-name"


# ---------------------------------------------------------------------------
# Reads are side-effect free; WS join still creates
# ---------------------------------------------------------------------------

def test_get_missing_lobby_returns_404_and_creates_nothing(client):
    r = client.get("/api/lobby/nope")
    assert r.status_code == 404
    assert api.lobbies.get("nope") is None
    assert client.get("/api/lobby").json()["lobbies"] == []


def test_game_create_on_missing_lobby_returns_404(client):
    r = client.post("/api/lobby/nope/game")
    assert r.status_code == 404
    assert api.lobbies.get("nope") is None


def test_legal_moves_on_missing_lobby_returns_404(client):
    r = client.get(
        "/api/lobby/nope/game/00000000-0000-0000-0000-000000000000/legal-moves",
        params={"r": 1, "c": 4},
    )
    assert r.status_code == 404
    assert api.lobbies.get("nope") is None


def test_ws_join_to_new_name_creates_lobby(client, ws_connect):
    ws = ws_connect("brand-new", token="tok-a")
    assert ws.receive_json() == {"color": "white"}
    r = client.get("/api/lobby/brand-new")
    assert r.status_code == 200
    assert r.json() == {"name": "brand-new", "game_id": None}


def test_lobby_service_getitem_does_not_create():
    svc = LobbyService()
    with pytest.raises(KeyError):
        svc["missing"]
    assert svc.get("missing") is None


def test_lobby_service_get_or_create_creates_once():
    svc = LobbyService()
    first = svc.get_or_create("x")
    assert svc.get_or_create("x") is first

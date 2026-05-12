import re
import pytest

from pydantic import BaseModel

from chakes.backend.models import ActiveGame, GameDef, Pos
from chakes.backend.services import ChakesService, ConnectionManager, LobbyService


# ---------------------------------------------------------------------------
# LobbyService
# ---------------------------------------------------------------------------

def test_lobby_service_getitem_auto_creates_missing_lobby():
    svc = LobbyService()
    lobby = svc["new-lobby"]
    assert lobby.name == "new-lobby"


def test_lobby_service_create_no_name_returns_adjective_animal():
    svc = LobbyService()
    lobby = svc.create()
    assert re.fullmatch(r"[a-z]+-[a-z]+", lobby.name), f"unexpected name: {lobby.name!r}"


def test_lobby_service_remove_is_idempotent():
    svc = LobbyService()
    svc.create("alpha")
    svc.remove("alpha")
    svc.remove("alpha")  # second call must not raise


def test_lobby_service_remove_deletes_lobby():
    svc = LobbyService()
    svc.create("beta")
    svc.remove("beta")
    assert svc.get("beta") is None


# ---------------------------------------------------------------------------
# ChakesService — move dispatch
# ---------------------------------------------------------------------------

def test_chakes_service_legal_moves_for_center_pawn_non_empty():
    lobbies = LobbyService()
    svc = ChakesService(lobbies)
    lobbies["test-lobby"]
    game = svc.create_game("test-lobby", GameDef())
    moves = svc.get_legal_moves("test-lobby", game.id, Pos(x=4, y=1))
    assert len(moves) > 0


def test_chakes_service_applying_legal_move_mutates_board():
    lobbies = LobbyService()
    svc = ChakesService(lobbies)
    lobbies["test-lobby"]
    game = svc.create_game("test-lobby", GameDef())

    src = Pos(x=4, y=1)
    [[dx, dy]] = svc.get_legal_moves("test-lobby", game.id, src)[:1]

    from chakes.backend.models import MoveRequest
    result = svc.move("test-lobby", game.id, MoveRequest(src=src, dst=Pos(x=dx, y=dy)))

    assert result is not None
    assert result._get_piece(Pos(x=dx, y=dy)) is not None
    assert result._get_piece(src) is None


# ---------------------------------------------------------------------------
# ConnectionManager.broadcast
# ---------------------------------------------------------------------------

class _OkWebSocket:
    def __init__(self):
        self.received: list[str] = []

    async def send_text(self, payload: str) -> None:
        self.received.append(payload)


class _FailWebSocket:
    async def send_text(self, payload: str) -> None:
        raise RuntimeError("connection dropped")


class _Msg(BaseModel):
    text: str


async def test_broadcast_delivers_to_healthy_socket_despite_failing_one():
    mgr = ConnectionManager()
    good = _OkWebSocket()
    bad = _FailWebSocket()
    mgr._connections["room"] = [bad, good]

    await mgr.broadcast("room", _Msg(text="hello"))

    assert len(good.received) == 1
    assert "hello" in good.received[0]


async def test_broadcast_does_not_propagate_exception_from_failing_socket():
    mgr = ConnectionManager()
    bad = _FailWebSocket()
    mgr._connections["room"] = [bad]

    await mgr.broadcast("room", _Msg(text="hi"))  # must not raise

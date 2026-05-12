import re

from pydantic import BaseModel

from chakes.backend.models import GameDef, Lobby, MoveRequest, Pos, summarize
from chakes.backend.server_identity import generate_server_name
from chakes.backend.services import ChakesService, ConnectionManager, LobbyService
from chakes.engine.engine import Player


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


# ---------------------------------------------------------------------------
# Server identity
# ---------------------------------------------------------------------------

def test_generate_server_name_matches_format():
    assert re.fullmatch(r"[a-z]+-[a-z]+", generate_server_name())


def test_server_name_constant_is_stable_within_process():
    from chakes.backend.server_identity import SERVER_NAME as sn1
    from chakes.backend.server_identity import SERVER_NAME as sn2
    assert sn1 is sn2


# ---------------------------------------------------------------------------
# ActiveGame winner caching
# ---------------------------------------------------------------------------

def _service_with_game(game_def: GameDef = GameDef()):
    lobbies = LobbyService()
    svc = ChakesService(lobbies)
    lobbies["test"]
    game = svc.create_game("test", game_def)
    return svc, game


def test_active_game_winner_cached_after_terminal_snapshot():
    svc, game = _service_with_game()
    game.snapshot = lambda: ({}, Player.WHITE)
    svc.move("test", game.id, MoveRequest(src=Pos(x=4, y=1), dst=Pos(x=4, y=2)))
    assert game.winner == "white"


def test_active_game_timestamp_end_set_when_winner_decided():
    svc, game = _service_with_game()
    game.snapshot = lambda: ({}, Player.WHITE)
    svc.move("test", game.id, MoveRequest(src=Pos(x=4, y=1), dst=Pos(x=4, y=2)))
    assert game.timestamp_end is not None


def test_active_game_timestamp_end_not_overwritten_on_subsequent_snapshots():
    svc, game = _service_with_game()
    game.snapshot = lambda: ({}, Player.WHITE)
    svc.move("test", game.id, MoveRequest(src=Pos(x=4, y=1), dst=Pos(x=4, y=2)))
    first_ts = game.timestamp_end
    # game.winner is now set; caching branch is skipped on the next move
    svc.move("test", game.id, MoveRequest(src=Pos(x=4, y=6), dst=Pos(x=4, y=5)))
    assert game.timestamp_end is first_ts


def test_active_game_winner_remains_none_while_game_in_progress():
    svc, game = _service_with_game()
    svc.move("test", game.id, MoveRequest(src=Pos(x=4, y=1), dst=Pos(x=4, y=2)))
    assert game.winner is None


# ---------------------------------------------------------------------------
# Lobby summary
# ---------------------------------------------------------------------------

class _FakeWS:
    pass


def _connections_with(lobby_name: str, count: int) -> ConnectionManager:
    mgr = ConnectionManager()
    if count > 0:
        mgr._connections[lobby_name] = [_FakeWS() for _ in range(count)]
    return mgr


def test_summarize_waiting_state_when_no_game():
    lobby = Lobby("test")
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.state == "waiting"


def test_summarize_waiting_state_has_null_settings():
    lobby = Lobby("test")
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.settings is None


def test_summarize_in_progress_state_when_game_started_and_no_winner():
    lobby = Lobby("test")
    lobby.create_game(GameDef())
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.state == "in_progress"


def test_summarize_in_progress_state_includes_settings():
    lobby = Lobby("test")
    lobby.create_game(GameDef())
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.settings is not None


def test_summarize_ended_state_when_winner_set():
    lobby = Lobby("test")
    game = lobby.create_game(GameDef())
    game.winner = "white"
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.state == "ended"


def test_summarize_zero_players_when_no_tokens_assigned():
    lobby = Lobby("test")
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.players == 0


def test_summarize_one_player_when_one_color_slot_filled():
    lobby = Lobby("test")
    lobby.assign_color("tok-a")
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.players == 1


def test_summarize_two_players_when_both_color_slots_filled():
    lobby = Lobby("test")
    lobby.assign_color("tok-a")
    lobby.assign_color("tok-b")
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.players == 2


def test_summarize_spectators_equals_connections_minus_players():
    lobby = Lobby("test")
    lobby.assign_color("tok-a")
    lobby.assign_color("tok-b")
    mgr = _connections_with("test", 5)
    result = summarize(lobby, mgr, "srv")
    assert result.spectators == 3


def test_summarize_spectators_non_negative_when_connections_below_player_count():
    lobby = Lobby("test")
    lobby.assign_color("tok-a")
    lobby.assign_color("tok-b")
    mgr = _connections_with("test", 1)
    result = summarize(lobby, mgr, "srv")
    assert result.spectators == 0


def test_summarize_anonymous_connections_count_as_spectators():
    lobby = Lobby("test")
    lobby.assign_color("tok-a")  # 1 player
    mgr = _connections_with("test", 2)  # 2 connections: 1 player + 1 anon
    result = summarize(lobby, mgr, "srv")
    assert result.spectators == 1


def test_summarize_settings_game_type_id_matches_game_def():
    lobby = Lobby("test")
    lobby.create_game(GameDef(game_type="orthodox"))
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.settings.game_type_id == "orthodox"


def test_summarize_settings_game_type_label_matches_game_types_table():
    lobby = Lobby("test")
    lobby.create_game(GameDef(game_type="orthodox"))
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.settings.game_type_label == "Orthodox"


def test_summarize_settings_pieces_include_orthodox_defaults():
    lobby = Lobby("test")
    lobby.create_game(GameDef(game_type="orthodox"))
    result = summarize(lobby, ConnectionManager(), "srv")
    names = [p.name for p in result.settings.pieces]
    assert "Pawn" in names
    assert "King" in names


def test_summarize_settings_cooldown_override_reflected():
    lobby = Lobby("test")
    lobby.create_game(GameDef(cooldowns={"Queen": 7}))
    result = summarize(lobby, ConnectionManager(), "srv")
    queen = next(p for p in result.settings.pieces if p.name == "Queen")
    assert queen.cooldown == 7.0


def test_summarize_settings_pieces_reflect_game_type_specific_set():
    lobby = Lobby("test")
    lobby.create_game(GameDef(game_type="knighted"))
    result = summarize(lobby, ConnectionManager(), "srv")
    names = [p.name for p in result.settings.pieces]
    assert "Archbishop" in names
    assert "Chancellor" in names


def test_summarize_settings_upside_down_flag_present():
    lobby = Lobby("test")
    lobby.create_game(GameDef(upside_down=True))
    result = summarize(lobby, ConnectionManager(), "srv")
    assert result.settings.upside_down is True


def test_summarize_server_name_attached_to_each_summary():
    lobby = Lobby("test")
    result = summarize(lobby, ConnectionManager(), "my-server")
    assert result.server_name == "my-server"

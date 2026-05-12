import pytest

from chakes.backend.models import (
    ActiveGame,
    GameDef,
    Lobby,
    GAME_TYPES,
    _DEFAULT_PIECE_NAMES,
)


# ---------------------------------------------------------------------------
# Lobby.assign_color
# ---------------------------------------------------------------------------

def test_assign_color_first_tokened_joiner_gets_white():
    lobby = Lobby("test")
    assert lobby.assign_color("token-a") == "white"


def test_assign_color_second_tokened_joiner_gets_black():
    lobby = Lobby("test")
    lobby.assign_color("token-a")
    assert lobby.assign_color("token-b") == "black"


def test_assign_color_third_tokened_joiner_becomes_spectator():
    lobby = Lobby("test")
    lobby.assign_color("token-a")
    lobby.assign_color("token-b")
    assert lobby.assign_color("token-c") == "spectator"


def test_assign_color_same_token_rejoining_is_idempotent():
    lobby = Lobby("test")
    first = lobby.assign_color("token-a")
    second = lobby.assign_color("token-a")
    assert first == second == "white"


def test_assign_color_anonymous_does_not_occupy_slot():
    lobby = Lobby("test")
    first = lobby.assign_color(None)
    second = lobby.assign_color(None)
    assert first == "white"
    assert second == "white"


def test_assign_color_anonymous_does_not_block_tokened_joiner():
    lobby = Lobby("test")
    lobby.assign_color(None)  # anonymous join
    assert lobby.assign_color("token-a") == "white"


# ---------------------------------------------------------------------------
# GameDef.get_piece_defs
# ---------------------------------------------------------------------------

def test_get_piece_defs_default_returns_standard_names():
    gd = GameDef()
    names = [pd.name for pd in gd.get_piece_defs()]
    assert names == _DEFAULT_PIECE_NAMES


def test_get_piece_defs_explicit_piece_defs_honored():
    gd = GameDef(piece_defs=["Pawn", "King"])
    names = [pd.name for pd in gd.get_piece_defs()]
    assert names == ["Pawn", "King"]


def test_get_piece_defs_cooldown_override_sets_value():
    gd = GameDef(cooldowns={"Queen": 5})
    defs = {pd.name: pd.value for pd in gd.get_piece_defs()}
    assert defs["Queen"] == 5


def test_get_piece_defs_non_overridden_pieces_keep_default_value():
    gd = GameDef(cooldowns={"Queen": 5})
    defs = {pd.name: pd.value for pd in gd.get_piece_defs()}
    assert defs["Pawn"] == 3  # engine default


def test_get_piece_defs_with_state_uses_board_pieces():
    from chakes.engine.engine import Board
    state = Board.knighted_chess()
    gd = GameDef(game_type="knighted")
    names = [pd.name for pd in gd.get_piece_defs(state=state)]
    assert "Archbishop" in names
    assert "Chancellor" in names


def test_get_piece_defs_with_state_differs_from_orthodox():
    from chakes.engine.engine import Board
    orthodox_state = Board.orthodox()
    knighted_state = Board.knighted_chess()
    gd = GameDef()
    orthodox_names = [pd.name for pd in gd.get_piece_defs(state=orthodox_state)]
    knighted_names = [pd.name for pd in gd.get_piece_defs(state=knighted_state)]
    assert orthodox_names != knighted_names


# ---------------------------------------------------------------------------
# ActiveGame construction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("game_type", list(GAME_TYPES.keys()))
def test_active_game_instantiates_for_all_game_types(game_type):
    game = ActiveGame(GameDef(game_type=game_type))
    assert game.id is not None
    assert game.state is not None


def test_active_game_upside_down_swaps_starting_ranks():
    normal = ActiveGame(GameDef(game_type="orthodox"))
    flipped = ActiveGame(GameDef(game_type="orthodox", upside_down=True))

    def owner_at(game, x, y):
        from chakes.backend.models import Pos
        piece = game._get_piece(Pos(x=x, y=y))
        return piece.owner.name if piece else None

    # Normal: row 0 is WHITE, row 7 is BLACK
    assert owner_at(normal, 0, 0) == "WHITE"
    assert owner_at(normal, 0, 7) == "BLACK"
    # Flipped: row 0 is BLACK, row 7 is WHITE
    assert owner_at(flipped, 0, 0) == "BLACK"
    assert owner_at(flipped, 0, 7) == "WHITE"


def test_active_game_cooldown_override_mutates_live_pieces():
    game = ActiveGame(GameDef(cooldowns={"Queen": 99}))
    queens = [p for p in game.state.all_pieces() if p.name == "Queen"]
    assert len(queens) > 0
    assert all(p.value == 99 for p in queens)


def test_active_game_cooldown_override_does_not_affect_other_pieces():
    game = ActiveGame(GameDef(cooldowns={"Queen": 99}))
    pawns = [p for p in game.state.all_pieces() if p.name == "Pawn"]
    assert all(p.value != 99 for p in pawns)


# ---------------------------------------------------------------------------
# ActiveGame winner caching (initial state)
# ---------------------------------------------------------------------------

def test_active_game_winner_starts_as_none():
    game = ActiveGame(GameDef())
    assert game.winner is None


def test_active_game_timestamp_end_starts_as_none():
    game = ActiveGame(GameDef())
    assert game.timestamp_end is None

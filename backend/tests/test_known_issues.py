import pytest

from chakes.engine.engine import Player
from chakes.backend.messages import GameStateMessage
from chakes.backend.models import ActiveGame, GameDef


@pytest.mark.xfail(
    reason="NEUTRAL winner serializes to 'black' instead of 'neutral':"
           " messages.py uses `winner.name == 'WHITE'` with no NEUTRAL branch",
    strict=True,
)
def test_neutral_winner_serializes_as_neutral():
    game = ActiveGame(GameDef())
    game.snapshot = lambda: ({}, Player.NEUTRAL)
    msg = GameStateMessage.from_active_game(game)
    assert msg.winner == "neutral"


@pytest.mark.xfail(
    reason="Unknown game_type silently falls back to orthodox instead of raising:"
           " ActiveGame uses dict.get(..., GAME_TYPES['orthodox']) with no validation",
    strict=True,
)
def test_unknown_game_type_raises():
    with pytest.raises(Exception):
        ActiveGame(GameDef(game_type="not-a-real-game"))

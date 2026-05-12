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
    game.snapshot = lambda: ({}, Player.NEUTRAL)  # type: ignore
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


@pytest.mark.xfail(
    reason="Lobbies created via POST /api/lobby with no subsequent WS connection persist "
           "forever; no TTL implemented. See follow-up #1 in PLAN_lobby_browser.md.",
    strict=True,
)
def test_lobby_created_without_ws_join_is_eventually_cleaned_up(client):
    client.post("/api/lobby", params={"name": "ttl-lobby"})
    r = client.get("/api/lobby")
    names = [e["name"] for e in r.json()["lobbies"]]
    assert "ttl-lobby" not in names

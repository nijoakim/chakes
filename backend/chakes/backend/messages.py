from pydantic import BaseModel

from chakes.backend.models import ActiveGame
from chakes.engine.engine import Player


class LobbyJoinedMessage(BaseModel):
    color: str


class GameStateMessage(BaseModel):
    board: list[list[dict | None]]
    cooldowns: list[list[float]]
    max_cooldowns: dict[str, float]
    piece_names: list[str]
    game_id: str
    winner: str | None = None  # excluded from wire when None (see ConnectionManager.broadcast)
    legal_moves: dict[str, list[list[int]]] = {}
    white_in_check: bool = False
    black_in_check: bool = False
    white_in_anti_check: bool = False
    black_in_anti_check: bool = False

    @classmethod
    def from_active_game(cls, game: ActiveGame) -> "GameStateMessage":
        all_moves, winner = game.snapshot()
        return cls(
            board=game.serialize_board(),
            cooldowns=game.serialize_cooldowns(),
            max_cooldowns=game.serialize_max_cooldowns(),
            piece_names=game.serialize_piece_names(),
            game_id=str(game.id),
            winner=("white" if winner.name == "WHITE" else "black") if winner else None,
            legal_moves=game.serialize_legal_moves(all_moves),
            white_in_check=game.state.is_in_check(Player.WHITE),
            black_in_check=game.state.is_in_check(Player.BLACK),
            white_in_anti_check=game.state.is_in_anti_check(Player.WHITE),
            black_in_anti_check=game.state.is_in_anti_check(Player.BLACK),
        )

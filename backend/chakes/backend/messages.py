from pydantic import BaseModel

from chakes.backend.models import ActiveGame


class LobbyJoinedMessage(BaseModel):
    color: str


class GameStateMessage(BaseModel):
    board: list[list[dict | None]]
    cooldowns: list[list[float]]
    max_cooldowns: dict[str, float]
    piece_names: list[str]
    game_id: str
    winner: str | None = None  # excluded from wire when None (see ConnectionManager.broadcast)

    @classmethod
    def from_active_game(cls, game: ActiveGame) -> "GameStateMessage":
        winner = game.state.winner()
        return cls(
            board=game.serialize_board(),
            cooldowns=game.serialize_cooldowns(),
            max_cooldowns=game.serialize_max_cooldowns(),
            piece_names=game.serialize_piece_names(),
            game_id=str(game.id),
            winner=("white" if winner.name == "WHITE" else "black") if winner else None,
        )

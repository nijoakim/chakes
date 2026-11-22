from pydantic import BaseModel

from chakes.backend.models import ActiveGame, serialize_legal_moves, winner_name
from chakes.engine.engine import Player, Pos as EnginePos

Snapshot = tuple[dict[EnginePos, set[EnginePos]], Player | None]


class LobbyJoinedMessage(BaseModel):
    color: str


class AllLegalMovesMessage(BaseModel):
    """Background push of every piece's legal moves for board `version`."""
    legal_moves: dict[str, list[list[int]]]
    version: int
    winner: str | None = None  # excluded from wire when None, like GameStateMessage.winner


class GameStateMessage(BaseModel):
    board: list[list[dict[str, str] | None]]
    cooldowns: list[list[float]]
    max_cooldowns: dict[str, float] | None = None
    piece_names: list[str] | None = None
    game_id: str
    version: int
    winner: str | None = None  # excluded from wire when None (see ConnectionManager.broadcast)
    legal_moves: dict[str, list[list[int]]] | None = None  # excluded when None
    white_in_check: bool = False
    black_in_check: bool = False
    white_in_anti_check: bool = False
    black_in_anti_check: bool = False

    @classmethod
    def from_active_game(
        cls,
        game: ActiveGame,
        *,
        include_immutables: bool = True,
        include_legal_moves: bool = True,
        snapshot: Snapshot | None = None,
    ) -> "GameStateMessage":
        """`snapshot` (from game.snapshot()) avoids recomputing when the caller already has one."""
        legal_moves = None
        winner = game.winner  # latched by ActiveGame.record_winner()
        if include_legal_moves:
            all_moves, snapshot_winner = snapshot if snapshot is not None else game.snapshot()
            winner = winner_name(snapshot_winner) if snapshot_winner else game.winner
            legal_moves = serialize_legal_moves(all_moves)
        return cls(
            board=game.serialize_board(),
            cooldowns=game.serialize_cooldowns(),
            max_cooldowns=game.serialize_max_cooldowns() if include_immutables else None,
            piece_names=game.serialize_piece_names() if include_immutables else None,
            game_id=str(game.id),
            version=game.version,
            winner=winner,
            legal_moves=legal_moves,
            white_in_check=game.state.is_in_check(Player.WHITE),
            black_in_check=game.state.is_in_check(Player.BLACK),
            white_in_anti_check=game.state.is_in_anti_check(Player.WHITE),
            black_in_anti_check=game.state.is_in_anti_check(Player.BLACK),
        )

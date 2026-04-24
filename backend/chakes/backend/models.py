from datetime import datetime

from pydantic import BaseModel

from chakes.engine.game_engine import GameState, Piece


class MoveRequest(BaseModel):
    from_r: int
    from_c: int
    to_r: int
    to_c: int


def _piece_code(piece: Piece) -> str:
    letter = "N" if piece.name == "Knight" else piece.name[0]
    return letter if piece.owner.name == "WHITE" else letter.lower()


class GameRoom:
    # These should be owned by the engine.
    timestamp_start: datetime
    timestamp_end: datetime | None = None

    def __init__(self):
        self.state = GameState.default()
        self.timestamp_start = datetime.now()

    def _get_piece(self, c: int, r: int) -> Piece | None:
        return self.state.board[c][7 - r]

    def serialize_board(self) -> list[list[str]]:
        return [
            [_piece_code(p) if (p := self._get_piece(c, r)) else "" for c in range(8)]
            for r in range(8)
        ]

    def serialize_cooldowns(self) -> list[list[float]]:
        return [
            [p.get_cooldown() if (p := self._get_piece(c, r)) else 0.0 for c in range(8)]
            for r in range(8)
        ]

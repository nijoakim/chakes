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

    def serialize_board(self) -> list[list[str]]:
        result = []
        for r in range(8):
            y = 7 - r
            row = [
                _piece_code(self.state.board[c][y]) if self.state.board[c][y] else ""
                for c in range(8)
            ]
            result.append(row)
        return result

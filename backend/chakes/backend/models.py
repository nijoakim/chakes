import random
import uuid
from datetime import datetime

from pydantic import BaseModel

from chakes.engine.game_engine import GameState, Piece as EnginePiece, piece_defs as engine_piece_defs


# --- Name generation ---

_ADJECTIVES = [
    "ardent", "bold", "calm", "deft", "eager", "fierce", "gentle", "hardy",
    "iron", "jolly", "keen", "lofty", "merry", "noble", "odd", "proud",
    "quick", "rustic", "sharp", "tidy", "unique", "vivid", "witty", "zesty",
]

_ANIMALS = [
    "aardvark", "badger", "cobra", "donkey", "eagle", "falcon", "gecko",
    "heron", "iguana", "jackal", "koala", "lemur", "moose", "newt",
    "otter", "panda", "quail", "raven", "sloth", "tiger", "urchin",
    "viper", "walrus", "yak", "zebra",
]


def generate_lobby_name() -> str:
    return f"{random.choice(_ADJECTIVES)}-{random.choice(_ANIMALS)}"


# --- Pydantic models (data transfer) ---


class MoveRequest(BaseModel):
    from_r: int
    from_c: int
    to_r: int
    to_c: int


class PieceDef(BaseModel):
    name: str
    value: int
    moveset: str


class Piece(BaseModel):
    name: str
    owner: str  # "white" or "black"
    row: int
    col: int
    cooldown: float


class GameDef(BaseModel):
    piece_defs: list[str] | None = None  # piece names to include; None = orthodox default

    def get_piece_defs(self) -> list[PieceDef]:
        names = self.piece_defs if self.piece_defs else [
            "Pawn", "Rook", "Knight", "Bishop", "Queen", "King",
        ]
        return [
            PieceDef(name=n, value=engine_piece_defs[n][0], moveset=engine_piece_defs[n][1])
            for n in names
        ]


class Game(BaseModel):
    id: uuid.UUID
    piece_defs: list[PieceDef]
    pieces: list[Piece]
    timestamp_start: datetime
    timestamp_end: datetime | None = None


# --- Internal state ---


def _piece_code(piece: EnginePiece) -> str:
    letter = "N" if piece.name == "Knight" else piece.name[0]
    return letter if piece.owner.name == "WHITE" else letter.lower()


class ActiveGame:
    def __init__(self, game_def: GameDef):
        self.id = uuid.uuid4()
        self.state = GameState.default()
        self.game_def = game_def
        self.timestamp_start = datetime.now()
        self.timestamp_end: datetime | None = None

    def _get_piece(self, c: int, r: int) -> EnginePiece | None:
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

    def get_legal_moves(self, r: int, c: int) -> list[list[int]]:
        """Return legal moves for the piece at board position (r, c) as [[r, c], ...]."""
        piece = self._get_piece(c, r)
        if piece is None:
            return []
        engine_moves = piece.legal_moves()
        return [[7 - ey, ex] for ex, ey in engine_moves]

    def to_game(self) -> Game:
        pieces = []
        for r in range(8):
            for c in range(8):
                p = self._get_piece(c, r)
                if p:
                    pieces.append(Piece(
                        name=p.name,
                        owner="white" if p.owner.name == "WHITE" else "black",
                        row=r,
                        col=c,
                        cooldown=p.get_cooldown(),
                    ))
        return Game(
            id=self.id,
            piece_defs=self.game_def.get_piece_defs(),
            pieces=pieces,
            timestamp_start=self.timestamp_start,
            timestamp_end=self.timestamp_end,
        )


class Lobby:
    def __init__(self, name: str):
        self.name = name
        self.game: ActiveGame | None = None

    def create_game(self, game_def: GameDef) -> ActiveGame:
        self.game = ActiveGame(game_def)
        return self.game

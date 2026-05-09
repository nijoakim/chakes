import random
import uuid
from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel

from chakes.engine.engine import Board as GameState, Piece as EnginePiece, Pos, piece_defs as engine_piece_defs

GAME_TYPES: dict[str, tuple[str, Callable[[], GameState]]] = {
    "orthodox":      ("Orthodox",      GameState.orthodox),
    "chess960":      ("Chess 960",     GameState.chess960),
    "berolina":      ("Berolina",      GameState.berolina_chess),
    "anti_king":     ("Anti-King",     GameState.anti_king_chess),
    "knighted":      ("Knighted",      GameState.knighted_chess),
}


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
    promotion: str | None = None


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


_DEFAULT_PIECE_NAMES = ["Pawn", "Rook", "Knight", "Bishop", "Queen", "King"]


class GameDef(BaseModel):
    piece_defs: list[str] | None = None  # piece names to include; None = orthodox default
    cooldowns: dict[str, float] | None = None  # per-piece-type cooldown override
    game_type: str = "orthodox"
    upside_down: bool = False

    def get_piece_defs(self, state: "GameState | None" = None) -> list[PieceDef]:
        if state is not None:
            seen: set[str] = set()
            names: list[str] = []
            for piece in state.all_pieces():
                if piece.name not in seen:
                    seen.add(piece.name)
                    names.append(piece.name)
        else:
            names = self.piece_defs if self.piece_defs else _DEFAULT_PIECE_NAMES
        cooldowns = self.cooldowns or {}
        return [
            PieceDef(
                name=n,
                value=int(cooldowns.get(n, engine_piece_defs[n][0])),
                moveset=engine_piece_defs[n][1],
            )
            for n in names
        ]


class Game(BaseModel):
    id: uuid.UUID
    piece_defs: list[PieceDef]
    pieces: list[Piece]
    timestamp_start: datetime
    timestamp_end: datetime | None = None


# --- Internal state ---


class ActiveGame:
    def __init__(self, game_def: GameDef):
        self.id = uuid.uuid4()
        factory = GAME_TYPES.get(game_def.game_type, GAME_TYPES["orthodox"])[1]
        self.state = factory()
        self.game_def = game_def
        self.timestamp_start = datetime.now()
        self.timestamp_end: datetime | None = None

        if game_def.upside_down:
            for piece in self.state.all_pieces():
                piece.owner = piece.owner.other()

        if game_def.cooldowns:
            for piece in self.state.all_pieces():
                if piece.name in game_def.cooldowns:
                    piece.value = int(game_def.cooldowns[piece.name])

    def _get_piece(self, c: int, r: int) -> EnginePiece | None:
        return self.state.piece_at(Pos(c, self.state.size_y - 1 - r))

    def serialize_board(self) -> list[list[dict | None]]:
        return [
            [
                {"name": p.name, "owner": "white" if p.owner.name == "WHITE" else "black"}
                if (p := self._get_piece(c, r)) else None
                for c in range(self.state.size_x)
            ]
            for r in range(self.state.size_y)
        ]

    def serialize_piece_names(self) -> list[str]:
        return [pd.name for pd in self.game_def.get_piece_defs(self.state)]

    def serialize_max_cooldowns(self) -> dict[str, float]:
        return {pd.name: float(pd.value) for pd in self.game_def.get_piece_defs(self.state)}

    def serialize_cooldowns(self) -> list[list[float]]:
        return [
            [p.get_cooldown() if (p := self._get_piece(c, r)) else 0.0 for c in range(self.state.size_x)]
            for r in range(self.state.size_y)
        ]

    def get_legal_moves(self, r: int, c: int) -> list[list[int]]:
        piece = self._get_piece(c, r)
        if piece is None:
            return []
        engine_moves = piece.legal_moves()
        return [[self.state.size_y - 1 - pos.y, pos.x] for pos in engine_moves]

    def to_game(self) -> Game:
        pieces = []
        for r in range(self.state.size_y):
            for c in range(self.state.size_x):
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
    _SLOTS = ("white", "black")

    def __init__(self, name: str):
        self.name = name
        self.game: ActiveGame | None = None
        self._token_colors: dict[str, str] = {}

    def assign_color(self, token: str | None) -> str:
        if token and token in self._token_colors:
            return self._token_colors[token]
        taken = set(self._token_colors.values())
        color = next((s for s in self._SLOTS if s not in taken), "black")
        if token:
            self._token_colors[token] = color
        return color

    def create_game(self, game_def: GameDef) -> ActiveGame:
        self.game = ActiveGame(game_def)
        return self.game

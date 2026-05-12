from __future__ import annotations

import random
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Literal

if TYPE_CHECKING:
    from chakes.backend.services import ConnectionManager

from pydantic import BaseModel, Field, TypeAdapter

from chakes.engine.engine import Board as GameState, Piece as EnginePiece, Pos as EnginePos, Player, piece_defs as engine_piece_defs

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

class Pos(BaseModel):
    x: int
    y: int

class MoveRequest(BaseModel):
    src : Pos
    dst : Pos
    promotion: str | None = None


# --- Incoming WebSocket message models ---

class PingMessage(BaseModel):
    type: Literal["ping"]
    id: str

class MoveMessage(BaseModel):
    type: Literal["move"]
    game_id: uuid.UUID
    src: Pos
    dst: Pos
    promotion: str | None = None
    client_move_id: str | None = None

class LegalMovesMessage(BaseModel):
    type: Literal["legal_moves"]
    game_id: uuid.UUID
    pos: Pos

IncomingMessage = Annotated[
    PingMessage | MoveMessage | LegalMovesMessage,
    Field(discriminator="type"),
]

INCOMING_ADAPTER: TypeAdapter[IncomingMessage] = TypeAdapter(IncomingMessage)


class PieceDef(BaseModel):
    name: str
    value: int
    moveset: str


class Piece(BaseModel):
    name: str
    owner: str  # "white" or "black"
    pos: Pos
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
        self.winner: str | None = None  # cached after first compute

        if game_def.upside_down:
            self.state.upside_down()

        if game_def.cooldowns:
            for piece in self.state.all_pieces():
                if piece.name in game_def.cooldowns:
                    piece.value = int(game_def.cooldowns[piece.name])

    def _get_piece(self, pos: Pos) -> EnginePiece | None:
        return self.state.piece_at(EnginePos(pos.x, pos.y))

    def serialize_board(self) -> list[list[dict | None]]:
        return [
            [
                {"name": p.name, "owner": "white" if p.owner.name == "WHITE" else "black"}
                if (p := self._get_piece(Pos(x=c, y=r))) else None
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
            [p.get_cooldown() if (p := self._get_piece(Pos(x=c, y=r))) else 0.0 for c in range(self.state.size_x)]
            for r in range(self.state.size_y)
        ]

    def serialize_legal_moves(
        self, all_moves: dict[EnginePos, set[EnginePos]]
    ) -> dict[str, list[list[int]]]:
        return {
            f"{src.x},{src.y}": sorted([p.x, p.y] for p in dests)
            for src, dests in all_moves.items()
        }

    def _winner_from(
        self, all_moves: dict[EnginePos, set[EnginePos]]
    ) -> "Player | None":
        for player in (Player.WHITE, Player.BLACK):
            player_dests: set[EnginePos] = set()
            for src, dests in all_moves.items():
                piece = self.state.piece_at(src)
                if piece is not None and piece.owner == player:
                    player_dests |= dests
            if player_dests == set():
                if not self.state.is_in_check(player) and not self.state.is_in_anti_check(player):
                    return Player.NEUTRAL
                return player.other()
        return None

    def snapshot(self) -> tuple[dict[EnginePos, set[EnginePos]], "Player | None"]:
        all_moves = self.state.all_legal_moves()
        winner = self._winner_from(all_moves)
        return all_moves, winner

    def get_legal_moves(self, pos: Pos) -> list[list[int]]:
        piece = self._get_piece(pos)
        if piece is None:
            return []
        engine_moves = piece.legal_moves()
        return [[p.x, p.y] for p in engine_moves]

    def to_game(self) -> Game:
        pieces = []
        for r in range(self.state.size_y):
            for c in range(self.state.size_x):
                pos = Pos(x=c, y=r)
                p = self._get_piece(pos)
                if p:
                    pieces.append(Piece(
                        name=p.name,
                        owner="white" if p.owner.name == "WHITE" else "black",
                        pos=pos,
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
        color = next((s for s in self._SLOTS if s not in taken), "spectator")
        if token:
            self._token_colors[token] = color
        return color

    def create_game(self, game_def: GameDef) -> ActiveGame:
        self.game = ActiveGame(game_def)
        return self.game


# --- Lobby summary (for list endpoint) ---

class PieceCooldown(BaseModel):
    name: str
    cooldown: float


class GameSettingsSummary(BaseModel):
    game_type_id: str
    game_type_label: str
    pieces: list[PieceCooldown]
    upside_down: bool


class LobbySummary(BaseModel):
    name: str
    server_name: str
    state: Literal["waiting", "in_progress", "ended"]
    players: int
    spectators: int
    settings: GameSettingsSummary | None


def summarize(lobby: Lobby, connections: ConnectionManager, server_name: str) -> LobbySummary:
    game = lobby.game
    if game is None:
        state: Literal["waiting", "in_progress", "ended"] = "waiting"
    elif game.winner is None:
        state = "in_progress"
    else:
        state = "ended"

    players = sum(
        1 for c in lobby._token_colors.values() if c in ("white", "black")
    )
    total = connections.connection_count(lobby.name)
    spectators = max(0, total - players)

    settings: GameSettingsSummary | None = None
    if game is not None:
        gd = game.game_def
        game_type_id = gd.game_type
        game_type_label = GAME_TYPES.get(game_type_id, ("Unknown", None))[0]
        cooldowns_map = game.serialize_max_cooldowns()
        pieces = [PieceCooldown(name=n, cooldown=c) for n, c in cooldowns_map.items()]
        settings = GameSettingsSummary(
            game_type_id=game_type_id,
            game_type_label=game_type_label,
            pieces=pieces,
            upside_down=gd.upside_down,
        )

    return LobbySummary(
        name=lobby.name,
        server_name=server_name,
        state=state,
        players=players,
        spectators=spectators,
        settings=settings,
    )

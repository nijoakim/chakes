"""Read-only catalogue data for the game-setup screen.

Human-readable descriptions of the game types and options, and per-piece
movement diagrams. The diagrams are not hand-written: they are measured by
asking the engine for a piece's legal moves on small boards (empty, with a
single enemy or friend on the target square, with blockers, with hurdles).
"""

from __future__ import annotations

from functools import cache
from typing import Any

from chakes.engine.engine import Board, Move, Piece, Player, Pos, piece_defs

# --- Descriptions -----------------------------------------------------------
#
# Written against the engine (Board.<factory>, Piece._move_special,
# Piece._legal_moves_special, Board.is_in_anti_check, Board.winner).

GAME_TYPE_DESCRIPTIONS: dict[str, str] = {
    "orthodox": (
        "The standard chess pieces and starting position on an 8x8 board. "
        "Pawns, castling, en passant and promotion work as usual; checkmate the enemy king to win."
    ),
    "chess960": (
        "Standard pieces, but the back rank is shuffled into one of 960 positions "
        "(bishops on opposite colours, king between the rooks), mirrored for black. "
        "A new random position is drawn when the game starts."
    ),
    "berolina": (
        "Orthodox chess with Berolina pawns: they move one square diagonally forward "
        "(two on their first move) and capture one square straight ahead. "
        "They promote as usual but cannot be taken en passant."
    ),
    "anti_king": (
        "Orthodox chess plus an Anti-King for each side, starting deep in enemy territory (d6 and d3). "
        "Your Anti-King must always be attacked by an enemy piece; a move that leaves it unattacked "
        "(anti-check) is illegal, just like leaving your king in check."
    ),
    "knighted": (
        "Played on a 10x8 board with two extra pieces per side: the Archbishop (bishop + knight) "
        "and the Chancellor (rook + knight), placed next to the bishops."
    ),
}

OPTION_DESCRIPTIONS: dict[str, str] = {
    "cooldown": (
        "There are no turns: both players move whenever they like. "
        "After a piece moves it must rest for its cooldown, in seconds, before it can move again."
    ),
    "upside_down": (
        "White starts on ranks 7-8 and black on ranks 1-2, but pawns keep their usual direction: "
        "they start stuck behind their own back rank and promote on reaching it."
    ),
}

PIECE_NOTES: dict[str, str] = {
    "Pawn": (
        "Promotes on the last rank. Can capture en passant a pawn that just made a double step, "
        "while that pawn is still on cooldown."
    ),
    "Berolina Pawn": "Promotes on the last rank. No en passant.",
    "King": (
        "Cannot be captured; you may not leave it in check. Castles by moving two squares towards "
        "an unmoved rook, which jumps to the square the king crossed."
    ),
    "Anti-King": (
        "Cannot be captured and cannot capture enemies, but may capture your own pieces. "
        "It must stay attacked by an enemy piece at all times."
    ),
    "Rook": "Moves together with the king when castling, and goes on cooldown too.",
    "Grasshopper": "Moves along queen lines but must jump over exactly one piece, landing just beyond it.",
    "Chameleon": "Changes after every move: knight, then bishop, rook, queen, and back to knight.",
}


def game_types_payload(game_types: dict[str, Any]) -> dict[str, Any]:
    """Body of GET /api/game-types: ids, labels and descriptions."""
    return {
        "game_types": [
            {
                "id": key,
                "name": label,
                "description": GAME_TYPE_DESCRIPTIONS.get(key, ""),
            }
            for key, (label, _) in game_types.items()
        ],
        "options": OPTION_DESCRIPTIONS,
    }


# --- Movement diagrams --------------------------------------------------------

GUIDE_SIZE = 9
_CENTRE = Pos(GUIDE_SIZE // 2, GUIDE_SIZE // 2)
_FILLER = "Pawn"  # name used for blockers / targets / hurdles; its own moves are never asked for


def _reach(
    name: str,
    extra: dict[Pos, Player],
    *,
    has_moved: bool = False,
) -> set[Pos]:
    board = Board(GUIDE_SIZE, GUIDE_SIZE)
    board.add_new_piece(name, Player.WHITE, _CENTRE)
    for pos, owner in extra.items():
        board.add_new_piece(_FILLER, owner, pos)
    piece = board.piece_at(_CENTRE)
    assert piece is not None
    piece.has_moved = has_moved
    return piece.legal_moves(check_safe=False)


def _hop_directions(name: str) -> set[Pos]:
    """Step vectors of the piece's hopping (hurdle-jumping) moves, if any."""
    directions: set[Pos] = set()
    for move in Piece.parse_moveset(piece_defs[name][1]):
        cur: Move | None = move
        while cur is not None:
            if cur.hops:
                directions |= cur.diff_poses
            cur = cur.compound
    return directions


def _squares() -> list[Pos]:
    return [
        Pos(x, y)
        for y in range(GUIDE_SIZE)
        for x in range(GUIDE_SIZE)
        if Pos(x, y) != _CENTRE
    ]


@cache
def piece_movement(name: str) -> dict[str, Any]:
    """Movement of a white piece from the centre of a GUIDE_SIZE board (white moves towards +y).

    Each reachable square is tagged with:
      move     - can move there when it is empty
      capture  - can capture an enemy standing there
      friend   - can capture a friendly piece standing there
      ride     - the move can be blocked by a piece on an intermediate square (slide/ride),
                 as opposed to a step or leap
      initial  - only possible while the piece has not moved yet
      hop      - only possible by jumping over a hurdle (see "hurdles")
    """
    empty = _reach(name, {})
    moved = _reach(name, {}, has_moved=True)

    tags: dict[Pos, dict[str, bool]] = {}

    def tag(pos: Pos) -> dict[str, bool]:
        return tags.setdefault(
            pos,
            {
                "move": False,
                "capture": False,
                "friend": False,
                "ride": False,
                "initial": False,
                "hop": False,
            },
        )

    for pos in _squares():
        if pos in empty:
            tag(pos)["move"] = True
        if pos in _reach(name, {pos: Player.BLACK}):
            tag(pos)["capture"] = True
        if pos in _reach(name, {pos: Player.WHITE}):
            tag(pos)["friend"] = True

    for pos, t in tags.items():
        if t["move"] and pos not in moved:
            t["initial"] = True

    # Slide/ride vs. step/leap: can a single piece elsewhere stop the move? Both the
    # blocked square and the square doing the blocking belong to a slide (so a rook's
    # first square counts as part of its slide, while a king's or knight's does not).
    reachable = set(tags)
    for pos, t in tags.items():
        if not t["move"]:
            continue
        for blocker in reachable - {pos}:
            if pos not in _reach(name, {blocker: Player.WHITE}):
                t["ride"] = True
                if tags[blocker]["move"]:
                    tags[blocker]["ride"] = True

    hurdles: list[Pos] = []
    if hop_directions := _hop_directions(name):
        # One hurdle two squares away along every hopping direction.
        hurdles = [_CENTRE + Pos(2 * d.x, 2 * d.y) for d in hop_directions]
        hurdle_map = dict.fromkeys(hurdles, Player.WHITE)
        with_hurdles = _reach(name, hurdle_map)
        for pos in with_hurdles - set(hurdles) - empty:
            t = tag(pos)
            t["hop"] = True
            t["move"] = True
            if pos in _reach(name, {**hurdle_map, pos: Player.BLACK}):
                t["capture"] = True

    return {
        "size": GUIDE_SIZE,
        "origin": {"x": _CENTRE.x, "y": _CENTRE.y},
        "squares": [
            {"x": pos.x, "y": pos.y, **t}
            for pos, t in sorted(tags.items(), key=lambda kv: (kv[0].y, kv[0].x))
        ],
        "hurdles": [
            {"x": h.x, "y": h.y} for h in sorted(hurdles, key=lambda p: (p.y, p.x))
        ],
    }


def piece_guide(names: list[str]) -> dict[str, Any]:
    """Body of GET /api/piece-guide."""
    return {
        "pieces": [
            {
                "name": n,
                "default_cooldown": piece_defs[n][0],
                "notes": PIECE_NOTES.get(n, ""),
                "movement": piece_movement(n),
            }
            for n in names
        ]
    }

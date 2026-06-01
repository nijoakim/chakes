# Copyright 2026 Joakim Nilsson

# This file is part of Chakes

# Chakes is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Chakes is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Chakes.  If not, see <https://www.gnu.org/licenses/>.


from __future__ import annotations

import re
import random
from enum import auto, Enum
from time import monotonic
from copy import deepcopy, copy
from dataclasses import dataclass


@dataclass(frozen = True)
class Pos:
    x: int
    y: int

    def __init__(self, str_or_x: str|int, y: int | None = None) -> None:
        if isinstance(str_or_x, str):
            x = ord(str_or_x[0]) - ord('a')
            y = int(str_or_x[1:]) - 1
        else:
            if y is None:
                raise TypeError("'x' is int, so 'y' must be int.")
            else:
                x = str_or_x

        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)

    def __str__(self) -> str:
        return chr(ord('a')+self.x) + str(self.y+1)

    def __repr__(self) -> str:
        return str(self)

    def __add__(self, other: Pos) -> Pos:
        return Pos(self.x+other.x, self.y+other.y)

    def __sub__(self, other: Pos) -> Pos:
        return Pos(self.x-other.x, self.y-other.y)

    def __neg__(self) -> Pos:
        return Pos(-self.x, -self.y)

class Player(Enum):
    WHITE   = auto()
    BLACK   = auto()
    NEUTRAL = auto()

    def other(self) -> Player:
        match self:
            case Player.WHITE:
                return Player.BLACK
            case Player.BLACK:
                return Player.WHITE
            case Player.NEUTRAL:
                return Player.NEUTRAL


# Format: name: (value, movement)
piece_defs: dict[str, tuple[int, str]] = {
    # Orthodox
    'Pawn':   (3, 'o1>,io2>,c1X>'),
    'Rook':   (3, 'n+'),
    'Knight': (3, '1/2'),
    'Bishop': (3, 'nX'),
    'Queen':  (3, 'n*'),
    'King':   (3, '1*'),

    # Fairy
    'Alibaba':       (3, '~2*'),
    'Alfil':         (3, '~2X'),
    'Amazon':        (3, 'n*,1/2'),
    'Anti-King':     (3, 'of1*'),
    'Archbishop':    (3, 'nX,1/2'),
    'Berolina Pawn': (3, 'o1X>,io2X>,c1>'),
    'Camel':         (3, '1/3'),
    'Chameleon':     (3, '1/2'),
    'Chancellor':    (3, 'n+,1/2'),
    'Commoner':      (3, '1*'),
    'Dabbaba':       (3, '~2+'),
    'Ferz':          (3, '1X'),
    'Ghost Bishop':  (3, '~nX'),
    'Ghost Queen':   (3, '~n*'),
    'Ghost Rook':    (3, '~n+'),
    'Grasshopper':   (3, '^n*'),
    'Gryphon':       (3, '1X.n+'),
    'Nightrider':    (3, 'n(1/2)'),
    'Skip Bishop':   (3, 'n(2/2)'),
    'Skip Queen':    (3, 'n(2/0),n(2/2)'),
    'Skip Rook':     (3, 'n(2/0)'),
    'Wazir':         (3, '1+'),
}


# TODO: @dataclass()
class Move:
    def __init__(
            self,
            capture_friend: bool,
            capture_enemy:  bool,
            capture_none:   bool,
            initial_only:   bool,
            leaps:          bool,
            hops:           bool,
            num_steps:      range,
        ):
        self.capture_friend: bool  = capture_friend
        self.capture_enemy:  bool  = capture_enemy
        self.capture_none:   bool  = capture_none
        self.initial_only:   bool  = initial_only
        self.leaps:          bool  = leaps
        self.hops:           bool  = hops
        self.num_steps:      range = num_steps

        self.diff_poses: set[Pos]    = set()
        self.compound:   Move | None = None

    def __str__(self) -> str:
        ret: str = ''

        ret += (
            f"{'i' if self.initial_only   else ''}"
            f"{'f' if self.capture_friend else ''}"
            f"{'c' if self.capture_enemy  else ''}"
            f"{'o' if self.capture_none   else ''}"
            f"{'~' if self.leaps          else ''}"
            f"{'^' if self.hops           else ''}"
            f", {self.num_steps}"
        )
        ret += ': ' + f'{ {str((diff_pos.x, diff_pos.y)) for diff_pos in self.diff_poses} }'.replace("'", '')[1:-1]

        if self.compound is not None:
            ret += f' . {self.compound}'

        return ret

    def __repr__(self) -> str:
        return str(self)


class Piece:
    movesets: dict[str, set[Move]] = {}

    def __init__(
        self, name: str, owner: Player, pos: Pos, board: Board
    ) -> None:
        self.name:  str    = name
        self.owner: Player = owner
        self.pos:   Pos    = pos
        self.board: Board  = board

        self.has_moved:      bool  = False
        self.last_move_time: float = -float('inf')

        # Piece definition
        self.value:   int = piece_defs[name][0]
        self.moveset: str = piece_defs[name][1]

        # Parse moveset if not already parsed
        if self.moveset not in Piece.movesets:
            Piece.movesets[self.moveset] = Piece.parse_moveset(self.moveset)

        self.captures: set[Piece] = set()

    def __str__(self) -> str:
        abbreviation: str = self.name[0] if self.name != 'Knight' else 'N'
        if self.get_cooldown() > 0:
            abbreviation = abbreviation.lower()

        color: str
        if self.owner == Player.WHITE:
            color = '\033[1;37m'
        elif self.owner == Player.BLACK:
            color = '\033[1;34m'

        return color + abbreviation + '\033[0m'

    def _capture(self, piece: Piece) -> None:
        self.captures.add(piece)
        self.board.remove_piece(piece)

    def _forwards(self) -> int:
        match self.owner:
            case Player.WHITE:
                return 1
            case Player.BLACK:
                return -1
            case _:
                return 0

    def _is_capture_move(self, pos: Pos) -> bool:
        piece: Piece | None = self.board.piece_at(pos)
        if piece is None:
            return False
        else:
            return piece.owner != self.owner

    def _legal_moves_in_direction(
        self,
        start_pos: Pos,
        diff_pos:  Pos,
        num_steps: int,
        leaps:     bool,
        hops:      bool,
    ) -> set[Pos]:
        if num_steps == 0:
            return set()

        new_pos: Pos = start_pos + diff_pos

        if not self.board.is_pos_within_board(new_pos):
            return set()

        new_piece: Piece | None = self.board.piece_at(new_pos)

        if hops:
            if new_piece is not None:
                return self._legal_moves_in_direction(new_pos, diff_pos, 1, leaps, False)
            else:
                return self._legal_moves_in_direction(new_pos, diff_pos, num_steps-1, leaps, True)

        # If square occupied
        if new_piece is not None:
            ret: set[Pos] = set()

            ret |= {new_pos}

            if leaps:
                ret |= self._legal_moves_in_direction(new_pos, diff_pos, num_steps-1, leaps, hops)

            return ret

        # If square unoccupied
        else:
            if num_steps > 1:
                return self._legal_moves_in_direction(new_pos, diff_pos, num_steps-1, leaps, hops)
            else:
                return {new_pos} | self._legal_moves_in_direction(new_pos, diff_pos, num_steps-1, leaps, hops)

    def move(
            self,
            new_pos:    Pos,
            info:       str = '',
            check_safe: bool = True
        ) -> None:
        if new_pos not in self.legal_moves(check_safe = check_safe):
            raise ValueError(f'{self.name} can not move from {self.pos} to {new_pos}.')

        if check_safe and (cooldown := self.get_cooldown()) != 0.0:
            raise ValueError(f'Cooldown for {self.name} at {self.pos} is {cooldown}')

        self._move_special(new_pos, info = info)

        other: Piece | None = self.board.piece_at(new_pos)
        if other is not None:
            self._capture(other)

        self.board.relocate_piece(self, new_pos)

        self.has_moved      = True
        self.last_move_time = monotonic()

    def _move_special(
            self,
            new_pos: Pos,
            info:    str = ''
        ) -> None:
        other: Piece | None

        match self.name:
            case 'Pawn':
                # Mark en passantable
                if abs(self.pos.y - new_pos.y) == 2:
                    self._en_passantable = True
                else:
                    self._en_passantable = False

                # Perform en passant
                if self.pos.x != new_pos.x:
                    other = self.board.piece_at(Pos(new_pos.x, self.pos.y))
                    if other is not None:
                        if getattr(other, '_en_passantable', False):
                            self._capture(other)

            case 'King':
                # Castling
                if abs(new_pos.x - self.pos.x) == 2:
                    diff_x: int = (new_pos.x - self.pos.x) // abs(new_pos.x - self.pos.x)
                    cur_x:  int = self.pos.x + diff_x
                    while self.board.is_pos_within_board(Pos(cur_x, self.pos.y)):
                        other = self.board.piece_at(Pos(cur_x, self.pos.y))
                        if other is not None:
                            if other.name == "Rook":
                                self.board.relocate_piece(other, Pos(self.pos.x+diff_x, self.pos.y))
                                other.last_move_time = monotonic()
                                return
                        cur_x += diff_x

            case 'Chameleon':
                # Shape shift
                if self.moveset == piece_defs['Knight'][1]:
                    self.value, self.moveset = piece_defs['Bishop']
                elif self.moveset == piece_defs['Bishop'][1]:
                    self.value, self.moveset = piece_defs['Rook']
                elif self.moveset == piece_defs['Rook'][1]:
                    self.value, self.moveset = piece_defs['Queen']
                elif self.moveset == piece_defs['Queen'][1]:
                    self.value, self.moveset = piece_defs['Knight']

        # Promote
        if 'Pawn' in self.name:
            if new_pos.y == 0 or new_pos.y == self.board.size_y-1:
                if info == '':
                    info = 'Queen'

                self.name = info

                self.value   = piece_defs[self.name][0]
                self.moveset = piece_defs[self.name][1]

    def get_cooldown(self) -> float:
        cooldown: float = self.last_move_time - monotonic() + self.value
        return max(cooldown, 0.0)

    def legal_moves(
            self,
            check_safe:      bool = True,
            invert_captures: bool = False,
        ) -> set[Pos]:
        ret: set[Pos] = set()

        move_dests: set[Pos] = set()
        poses:      set[Pos] = {self.pos}

        for move in Piece.movesets[self.moveset]:
            while True:
                for pos in poses:
                    for diff_pos in move.diff_poses:
                        diff_pos = Pos(diff_pos.x, self._forwards()*diff_pos.y)
                        for num_steps in move.num_steps:
                            move_dests |= self._legal_moves_in_direction(pos, diff_pos, num_steps, move.leaps, move.hops)

                capture_friend: bool = move.capture_friend
                capture_enemy:  bool = move.capture_enemy
                capture_none:   bool = move.capture_none

                # Invert captures
                if invert_captures:
                    capture_friend = capture_enemy
                    capture_enemy, capture_none = capture_none, capture_enemy

                # Filter out moves based on what/whether they capture
                move_dests = {
                    move_dest for move_dest in move_dests for piece in (self.board.piece_at(move_dest),)
                    if  (not move.initial_only or not self.has_moved)
                    and (
                        (capture_friend and piece is not None and piece.owner == self.owner)
                        or (capture_enemy  and piece is not None and piece.owner != self.owner)
                        or (capture_none   and piece is None)
                    )
                }

                ret |= move_dests

                if move.compound is None:
                    break
                else:
                    move       = move.compound
                    poses      = move_dests
                    move_dests = set()

        # Apply special rules
        moves = self._legal_moves_special(ret, check_safe = check_safe)

        return ret

    @staticmethod
    def parse_moveset(
            moveset_str: str,
        ) -> set[Move]:

        moveset: set[Move] = set()

        # Parse alternatives
        for pattern in moveset_str.split(','):
            last_move: Move | None = None

            # Parse compounds
            for pattern in pattern.split('.'):
                match: re.Match[str] | None = None

                num_steps_range: range

                capture_friend: bool = False
                capture_enemy:  bool = True
                capture_none:   bool = True
                initial_only:   bool = False

                leaps:          bool = False
                hops:           bool = False

                # Parse conditions
                if match := re.match(r'[f|c|o|i|]+', pattern):
                    capture_friend = 'f' in pattern
                    capture_enemy  = 'c' in pattern
                    capture_none   = 'o' in pattern
                    initial_only   = 'i' in pattern
                    pattern = pattern[match.end():]

                # Parse move type
                match pattern[0]:
                    case '~':
                        leaps = True
                        pattern = pattern[1:]
                    case '^':
                        hops = True
                        pattern = pattern[1:]

                # Parse number of steps
                if not re.match(r'\(?[0-9]+/', pattern):
                    # n
                    if pattern[0] == 'n':
                        num_steps_range = range(-1, 0)
                        pattern = pattern[1:]

                    # x-y
                    elif match := re.match(r'[0-9]+\-[0-9]+', pattern):
                        start, end = tuple([int(num) for num in pattern[:match.end()].split('-')])
                        if start >= end:
                            raise AssertionError(f'For number of steps range, {start} is larger than or equal to {end}.')
                        num_steps_range = range(start, end+1)
                        pattern = pattern[match.end():]

                    # x
                    elif match := re.match(r'[0-9]+', pattern):
                        num: int = int(pattern[:match.end()])
                        num_steps_range = range(num, num+1)
                        pattern = pattern[match.end():]
                else:
                    num_steps_range = range(1, 2)

                # Create move
                move: Move = Move(capture_friend, capture_enemy, capture_none, initial_only, leaps, hops, num_steps_range)

                # Attach move either to base moveset or to last move
                if last_move is None:
                    moveset.add(move)
                else:
                    last_move.compound = move

                # Update last move
                last_move = move

                # Parse parentheses
                if match := re.match(r'\(.*\)', pattern):
                    pattern = pattern[1:match.end()-1] + pattern[match.end():]

                # Parse direction
                if match := re.match(r'X>|X<|<>|>=|<=|>|<|=|\+|X|\*|[0-9]+/[0-9]+', pattern):
                    move_type: str = pattern[:match.end()]
                    pattern   = pattern[match.end():]

                    # For each number of steps
                    for num_steps in num_steps_range:
                        match move_type:
                            # Orthogonally forwards
                            case '>':
                                move.diff_poses.add(Pos(0, 1))

                            # Orthogonally backwards
                            case '<':
                                move.diff_poses.add(Pos(0, -1))

                            # Orthogonally forwards and backwards
                            case '<>':
                                for y in (-1, 1):
                                    move.diff_poses.add(Pos(0, y))

                            # Orthogonally sideways
                            case '=':
                                for y in (-1, 1):
                                    move.diff_poses.add(Pos(0, y))

                            # Orthogonally forwards and sideways
                            case '>=':
                                move.diff_poses.add(Pos(0, 1))
                                for x in (-1, 1):
                                    move.diff_poses.add(Pos(x, 0))

                            # Orthogonally backwards and sideways
                            case '<=':
                                move.diff_poses.add(Pos(0, -1))
                                for x in (-1, 1):
                                    move.diff_poses.add(Pos(x, 0))

                            # Diagonally forwards
                            case 'X>':
                                for x in -1, 1:
                                    move.diff_poses.add(Pos(x, 1))

                            # Diagonally backwards
                            case 'X<':
                                for x in -1, 1:
                                    move.diff_poses.add(Pos(x, -1))

                            # Orthogonally
                            case '+':
                                for x, y in (1, 0), (0, 1), (-1, 0), (0, -1):
                                    move.diff_poses.add(Pos(x, y))

                            # Diagonally
                            case 'X':
                                for x, y in (1, 1), (-1, 1), (1, -1), (-1, -1):
                                    move.diff_poses.add(Pos(x, y))

                            # Any direction
                            case '*':
                                for x, y in (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1):
                                    move.diff_poses.add(Pos(x, y))

                            # Hippogonally
                            case _ if '/' in move_type:
                                a: int
                                b: int
                                a, b = tuple([int(num_str) for num_str in move_type.split('/')][:2])
                                for c, d in ((a, b), (-a, b), (a, -b), (-a, -b)):
                                    for x, y in ((c, d), (d, c)):
                                        move.diff_poses.add(Pos(x, y))

        return moveset

    def _legal_moves_special(
            self,
            moves:      set[Pos],
            check_safe: bool = True,
        ) -> set[Pos]:
        other: Piece | None

        match self.name:
            case 'Pawn':
                # En passant
                for x, y in (self.pos.x-1, self.pos.y), (self.pos.x+1, self.pos.y):
                    if self.board.is_pos_within_board(Pos(x, y)):
                        other = self.board.piece_at(Pos(x, y))
                        if other is not None:
                            if getattr(other, '_en_passantable', False) \
                            and other.owner != self.owner \
                            and other.get_cooldown() > 0:
                                moves |= {Pos(x, y+self._forwards())}

            case 'King':
                # Castling
                attacked:     set[Pos] = self.board.attacked_squares(self.owner, invert_captures = False) if check_safe else set()
                attacked_inv: set[Pos] = self.board.attacked_squares(self.owner, invert_captures = True) if check_safe else set()
                for diff_x in (-1, 1):
                    if  self.pos not in attacked \
                    and self.pos + Pos(diff_x, 0) not in attacked_inv:
                        cur_x: int = self.pos.x + diff_x
                        while self.board.is_pos_within_board(Pos(cur_x, self.pos.y)):
                            other = self.board.piece_at(Pos(cur_x, self.pos.y))
                            if other is not None:
                                if other.name == 'Rook' \
                                and other.owner == self.owner \
                                and not self.has_moved \
                                and not other.has_moved \
                                and self.board.is_pos_within_board(self.pos + Pos(2*diff_x, 0)) \
                                and self.board.piece_at(Pos(self.pos.x+2*diff_x, self.pos.y)) is None:
                                    moves |= {self.pos + Pos(2*diff_x, 0)}
                                break
                            cur_x += diff_x

        # Filter unsafe moves
        if check_safe:
            for new_pos in set(moves):
                old_pos: Pos = self.pos

                # Test move
                self.board.move_piece(self.pos, new_pos, check_safe = False)

                # Remove move if in check or anti-check
                if self.board.is_in_anti_check(self.owner) \
                or self.board.is_in_check(self.owner):
                    moves -= {new_pos}

                # Revert test move
                self.board.revert_moves(1)

        # Filter moves that capture invincible pieces
        if check_safe:
            for pos in set(moves):
                other = self.board.piece_at(pos)
                if other is not None:
                    if other.name == 'King' \
                    or other.name == 'Anti-King':
                        moves -= {pos}

        return moves


class Board:
    pieces:   dict[Pos, Piece]
    move_log: list[tuple[Piece, Pos, set[Piece]]] # Format: (piece before move, destination, captures)

    def __init__(self, size_x: int = 8, size_y: int = 8, pieces: set[Piece] = set()) -> None:
        self.size_x: int = size_x
        self.size_y: int = size_y

        self.pieces   = {}
        self.move_log = []

        for piece in pieces:
            self.add_piece(piece)

    @staticmethod
    def orthodox() -> Board:
        board = Board(8, 8)

        board.add_new_piece_row('Pawn', Player.WHITE, '2')

        board.add_new_piece('Rook',   Player.WHITE, Pos('a1'))
        board.add_new_piece('Knight', Player.WHITE, Pos('b1'))
        board.add_new_piece('Bishop', Player.WHITE, Pos('c1'))
        board.add_new_piece('Queen',  Player.WHITE, Pos('d1'))
        board.add_new_piece('King',   Player.WHITE, Pos('e1'))
        board.add_new_piece('Bishop', Player.WHITE, Pos('f1'))
        board.add_new_piece('Knight', Player.WHITE, Pos('g1'))
        board.add_new_piece('Rook',   Player.WHITE, Pos('h1'))

        board.symmetry()

        return board

    @staticmethod
    def berolina_chess() -> Board:
        board = Board(8, 8)

        board.add_new_piece_row('Berolina Pawn', Player.WHITE, '2')

        board.add_new_piece('Rook',   Player.WHITE, Pos('a1'))
        board.add_new_piece('Knight', Player.WHITE, Pos('b1'))
        board.add_new_piece('Bishop', Player.WHITE, Pos('c1'))
        board.add_new_piece('Queen',  Player.WHITE, Pos('d1'))
        board.add_new_piece('King',   Player.WHITE, Pos('e1'))
        board.add_new_piece('Bishop', Player.WHITE, Pos('f1'))
        board.add_new_piece('Knight', Player.WHITE, Pos('g1'))
        board.add_new_piece('Rook',   Player.WHITE, Pos('h1'))

        board.symmetry()

        return board


    @staticmethod
    def anti_king_chess() -> Board:
        board = Board.orthodox()

        board.add_new_piece('Anti-King', Player.WHITE, Pos('d6'))
        board.add_new_piece('Anti-King', Player.BLACK, Pos('d3'))

        return board

    @staticmethod
    def chess960(n: int = -1) -> Board:
        b: int

        if n >= 960:
            raise ValueError('n must be lower than 960')

        if n < 0:
            n = random.randrange(960)

        board = Board(8, 8)

        board.add_new_piece_row('Pawn', Player.WHITE, '2')

        pieces: list[str | None] = 8 * [None]  # type: ignore[assignment]

        n, b = divmod(n, 4)
        pieces[b*2+1] = 'Bishop'

        n, b = divmod(n, 4)
        pieces[b*2] = 'Bishop'

        n, b = divmod(n, 6)
        for i, piece in enumerate(pieces):
            if piece is None:
                b -= 1
                if b == -1:
                    pieces[i] = 'Queen'

        n, b = \
            (n - 0, 0) if n <= 3 else \
            (n - 3, 1) if n <= 6 else \
            (n - 5, 2) if n <= 8 else \
            (n - 6, 3)

        for i, piece in enumerate(pieces):
            if piece is None:
                b -= 1
                if b == -1:
                    pieces[i] = 'Knight'

        for i, piece in enumerate(pieces):
            if piece is None:
                n -= 1
                if n == -1:
                    pieces[i] = 'Knight'

        for piece in ('Rook', 'King', 'Rook'):
            for i, _ in enumerate(pieces):
                if pieces[i] is None:
                    pieces[i] = piece
                    break

        board.add_new_piece_row(pieces, Player.WHITE, '1')
        board.symmetry()
        return board

    @staticmethod
    def knighted_chess() -> Board:
        board = Board(10, 8)

        board.add_new_piece_row('Pawn', Player.WHITE, '2')

        board.add_new_piece('Rook',       Player.WHITE, Pos('a1'))
        board.add_new_piece('Knight',     Player.WHITE, Pos('b1'))
        board.add_new_piece('Archbishop', Player.WHITE, Pos('c1'))
        board.add_new_piece('Bishop',     Player.WHITE, Pos('d1'))
        board.add_new_piece('Queen',      Player.WHITE, Pos('e1'))
        board.add_new_piece('King',       Player.WHITE, Pos('f1'))
        board.add_new_piece('Bishop',     Player.WHITE, Pos('g1'))
        board.add_new_piece('Chancellor', Player.WHITE, Pos('h1'))
        board.add_new_piece('Knight',     Player.WHITE, Pos('i1'))
        board.add_new_piece('Rook',       Player.WHITE, Pos('j1'))

        board.symmetry()

        return board

    def all_pieces(self) -> set[Piece]:
        return set(self.pieces.values())

    def piece_at(self, pos: Pos) -> Piece | None:
        return self.pieces.get(pos, None)

    def relocate_piece(self, piece: Piece, pos: Pos) -> None:
        self.remove_piece(piece)
        piece.pos = pos
        self.pieces[piece.pos] = piece

    def add_piece(self, piece: Piece) -> None:
        if not self.is_pos_within_board(piece.pos):
            raise RuntimeError(f'{piece.pos} is outside of the board.')

        if self.piece_at(piece.pos) is not None:
            raise RuntimeError(f'There is already a piece at {piece.pos}')

        self.pieces[piece.pos] = piece

    def add_new_piece(self, name: str, owner: Player, pos: Pos) -> None:
        if not self.is_pos_within_board(pos):
            raise RuntimeError(f'{pos} is outside of the board.')

        if self.piece_at(pos) is not None:
            raise RuntimeError(f'There is already a piece at {pos}')

        new_piece: Piece = Piece(name, owner, pos, self)
        self.pieces[pos] = new_piece

    def add_new_piece_row(self, names: str | list[str | None], owner: Player, row: int|str) -> None:
        y: int = row if isinstance(row, int) else int(row)-1

        for x in range(self.size_x):
            if isinstance(names, str):
                self.add_new_piece(names, owner, Pos(x, y))
            elif isinstance(names, list):
                name: str | None = names[x]
                if name is not None:
                    self.add_new_piece(name, owner, Pos(x, y))

    def remove_piece(self, piece: Piece) -> None:
        del self.pieces[piece.pos]

    def remove_piece_at(self, pos: Pos) -> None:
        del self.pieces[pos]

    def upside_down(self) -> None:
        # Rearrange position keys for pieces dictionary
        self.pieces = {Pos(piece.pos.x, self.size_y-1 - piece.pos.y): piece for piece in self.all_pieces()}

        # Update pieces' internal position
        for pos, piece in self.pieces.items():
            piece.pos = pos

    def symmetry(self) -> None:
        for piece in self.all_pieces():
            pos: Pos = Pos(piece.pos.x, self.size_y-1 - piece.pos.y)
            new_piece: Piece | None = self.piece_at(pos)
            if new_piece is not None:
                raise RuntimeError(f'Impossible to make symmetry due to {piece.name} at {piece.pos} and {new_piece.name} at {pos}.')
            self.add_new_piece(piece.name, piece.owner.other(), pos)

    def move_piece(
            self,
            pos1:       Pos,
            pos2:       Pos,
            info:       str  = '',
            check_safe: bool = True,
        ) -> None:
        piece: Piece | None = self.piece_at(pos1)
        if piece is None:
            raise ValueError(f'There is no piece at {pos1}.')
        else:
            piece_copy: Piece = copy(piece)
            piece.move(pos2, info = info, check_safe = check_safe)

        self.move_log.append((piece_copy, pos2, piece.captures))
        piece.captures = set()

    def revert_moves(self, n: int) -> None:
        if n <= 0:
            return
        else:
            piece_old, pos_new, captures = self.move_log.pop()

            # Restore old piece
            piece_new: Piece | None = self.piece_at(pos_new)
            assert piece_new is not None
            self.remove_piece_at(pos_new)
            piece_new.__dict__.update(piece_old.__dict__)
            piece_new.captures = set()
            self.add_piece(piece_new)

            for captured in captures:
                self.add_piece(captured)

            self.revert_moves(n-1)

    def is_pos_within_board(self, pos: Pos) -> bool:
        return \
            pos.x >= 0 and \
            pos.y >= 0 and \
            pos.x < self.size_x and \
            pos.y < self.size_y

    def attacked_squares(
            self,
            player:          Player,
            invert_captures: bool = False
        ) -> set[Pos]:
        return set.union(*[
            piece.legal_moves(check_safe = False, invert_captures = invert_captures)
            for piece in self.all_pieces()
            if piece.owner == player.other()
        ])

    def is_in_check(self, player: Player) -> bool:
        kings: set[Piece] = {
            piece for piece in self.all_pieces()
            if  piece.owner == player
            and piece.name == 'King'
        }
        attacked_kings: set[Piece] = {
            king for king in kings
            if king.pos in self.attacked_squares(player)
        }
        return attacked_kings & kings != set()

    def is_in_anti_check(self, player: Player) -> bool:
        anti_kings: set[Piece] = {
            piece for piece in self.all_pieces()
            if  piece.owner == player
            and piece.name == 'Anti-King'
        }
        attacked_anti_kings: set[Piece] = {
            anti_king for anti_king in anti_kings
            if anti_king.pos in self.attacked_squares(player)
        }
        return attacked_anti_kings != anti_kings

    def winner(self) -> Player | None:
        for player in (Player.WHITE, Player.BLACK):
            if set.union(*self.all_legal_moves(filter_player = player).values()) == set():
                # Draw if no kings under attack and all anti kings under attack
                if  not self.is_in_check(player) \
                and not self.is_in_anti_check(player):
                    return Player.NEUTRAL

                # Otherwise other player wins
                else:
                    return player.other()

        return None

    def all_legal_moves(self, filter_player: Player | None = None) -> dict[Pos, set[Pos]]:
        return {
            piece.pos: piece.legal_moves()
            for piece in self.all_pieces()
            if filter_player is None or piece.owner == filter_player
        }

    def __str__(self) -> str:
        ret: str = ''
        for y in reversed(range(self.size_y)):
            ret += f'\033[33m{str(Pos(0, y))[1:]} \033[0m'
            for x in range(self.size_x):
                piece = self.piece_at(Pos(x, y))
                ret += '.' if piece is None else str(piece)
                ret += ' ' if x < self.size_x else ''
            ret += '\n'
        ret = ret[:-1]
        ret += '\n  '
        ret += ' '.join([f'\033[33m{str(Pos(x, 0))[0]}' for x in range(self.size_x)])
        ret += '\033[0m'
        return ret

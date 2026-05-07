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
from typing import Optional
from copy import deepcopy
from dataclasses import dataclass


print('Hello Chakes!')


@dataclass(frozen = True)
class Pos:
    x: int
    y: int

    def __init__(self, str_or_x: str|int, y: Optional[int] = None) -> None:
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


class Piece:
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

    def _forwards(self) -> int:
        match self.owner:
            case Player.WHITE:
                return 1
            case Player.BLACK:
                return -1
            case _:
                return 0

    def _is_capture_move(self, pos: Pos) -> bool:
        piece: Optional[Piece] = self.board.piece_at(pos)
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

        new_piece: Optional[Piece] = self.board.piece_at(new_pos)

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

        self.board.relocate_piece(self, new_pos)

        self.has_moved      = True
        self.last_move_time = monotonic()

    def _move_special(
            self,
            new_pos: Pos,
            info:    str = ''
        ) -> None:
        other: Optional[Piece]

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
                            self.board.remove_piece(other)

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
        """
        Returns a set of legal moves for a piece.

        Args:
            check_safe:      Whether to exclude moves that are unsafe
            invert_captures: Whether to invert capturing and non-capturing moves

        Returns:
            Set of legal moves
        """

        moves: set[Pos] = set()

        # Parse alternatives
        for pattern in self.moveset.split(','):
            moves_alt:  set[Pos] = set()
            moves_comp: set[Pos] = {self.pos}

            # Parse compounds
            for pattern in pattern.split('.'):
                moves_comp_temp: set[Pos] = moves_comp
                moves_comp = set()
                for pos in moves_comp_temp:
                    pattern_temp = pattern

                    match: Optional[re.Match] = None

                    num_steps_range: range

                    capture_friend: bool = False
                    capture_enemy:  bool = True
                    capture_none:   bool = True

                    leaps:          bool = False
                    hops:           bool = False
                    unsafe:         bool = False

                    # Parse conditions
                    if match := re.match(r'[f|c|o|i|]+', pattern_temp):
                        pattern_temp = '_' if 'i' in pattern_temp and self.has_moved else pattern_temp.replace('i', '')
                    if match := re.match(r'[f|c|o|i|]+', pattern_temp):
                        capture_friend = 'f' in pattern_temp
                        capture_enemy  = 'c' in pattern_temp
                        capture_none   = 'o' in pattern_temp
                        pattern_temp = pattern_temp[match.end():]

                    # Invert captures
                    if invert_captures:
                        capture_friend = capture_enemy
                        capture_enemy, capture_none = capture_none, capture_enemy

                    # Parse move type
                    match pattern_temp[0]:
                        case '~':
                            leaps = True
                            pattern_temp = pattern_temp[1:]
                        case '^':
                            hops = True
                            pattern_temp = pattern_temp[1:]

                    # Parse number of steps
                    if not re.match(r'\(?[0-9]+/', pattern_temp):
                        # n
                        if pattern_temp[0] == 'n':
                            num_steps_range = range(-1, 0)
                            pattern_temp = pattern_temp[1:]

                        # x-y
                        elif match := re.match(r'[0-9]+\-[0-9]+', pattern_temp):
                            start, end = tuple([int(num) for num in pattern_temp[:match.end()].split('-')])
                            if start >= end:
                                raise AssertionError(f'For number of steps range in {self.name}, {start} is larger than or equal to {end}.')
                            num_steps_range = range(start, end+1)
                            pattern_temp = pattern_temp[match.end():]

                        # x
                        elif match := re.match(r'[0-9]+', pattern_temp):
                            num: int = int(pattern_temp[:match.end()])
                            num_steps_range = range(num, num+1)
                            pattern_temp = pattern_temp[match.end():]
                    else:
                        num_steps_range = range(1, 2)

                    # Parse parentheses
                    if match := re.match(r'\(.*\)', pattern_temp):
                        pattern_temp = pattern_temp[1:match.end()-1] + pattern_temp[match.end():]

                    # Parse direction
                    if match := re.match(r'X>|X<|<>|>=|<=|>|<|=|\+|X|\*|[0-9]+/[0-9]+', pattern_temp):
                        move_type: str = pattern_temp[:match.end()]
                        pattern_temp = pattern_temp[match.end():]

                        # For each number of steps
                        for num_steps in num_steps_range:
                            match move_type:
                                # Orthogonally forwards
                                case '>':
                                    moves_comp |= self._legal_moves_in_direction(pos, Pos(0, self._forwards()), num_steps, leaps, hops)

                                # Orthogonally backwards
                                case '<':
                                    moves_comp |= self._legal_moves_in_direction(pos, Pos(0, -self._forwards()), num_steps, leaps, hops)

                                # Orthogonally forwards and backwards
                                case '<>':
                                    for direction in (-1, 1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(0, direction), num_steps, leaps, hops)

                                # Orthogonally sideways
                                case '=':
                                    for direction in (-1, 1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(direction, 0), num_steps, leaps, hops)

                                # Orthogonally forwards and sideways
                                case '>=':
                                    moves_comp |= self._legal_moves_in_direction(pos, Pos(0, self._forwards()), num_steps, leaps, hops)
                                    for direction in (-1, 1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(direction, 0), num_steps, leaps, hops)

                                # Orthogonally backwards and sideways
                                case '<=':
                                    moves_comp |= self._legal_moves_in_direction(pos, Pos(0, -num_steps), 1, leaps, hops)
                                    for direction in (-1, 1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(direction*self._forwards(), 0), num_steps, leaps, hops)

                                # Diagonally forwards
                                case 'X>':
                                    y = self._forwards()
                                    for x in -1, 1:
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(x, y), num_steps, leaps, hops)

                                # Diagonally backwards
                                case 'X<':
                                    y = -self._forwards()
                                    for x in -1, 1:
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(x, y), num_steps, leaps, hops)

                                # Orthogonally
                                case '+':
                                    for x, y in (1, 0), (0, 1), (-1, 0), (0, -1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(x, y), num_steps, leaps, hops)

                                # Diagonally
                                case 'X':
                                    for x, y in (1, 1), (-1, 1), (1, -1), (-1, -1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(x, y), num_steps, leaps, hops)

                                # Any direction
                                case '*':
                                    for x, y in (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1):
                                        moves_comp |= self._legal_moves_in_direction(pos, Pos(x, y), num_steps, leaps, hops)

                                # Hippogonally
                                case _ if '/' in move_type:
                                    a: int
                                    b: int
                                    a, b = tuple([int(num_str) for num_str in move_type.split('/')][:2])
                                    for c, d in ((a, b), (-a, b), (a, -b), (-a, -b)):
                                        for x, y in ((c, d), (d, c)):
                                            moves_comp |= self._legal_moves_in_direction(pos, Pos(x, y), num_steps, leaps, hops)

                # Filter out moves based on what/whether they capture
                moves_comp = {
                    move for move in moves_comp for piece in (self.board.piece_at(move),)
                    if (capture_friend and piece is not None and piece.owner == self.owner)
                    or (capture_enemy  and piece is not None and piece.owner != self.owner)
                    or (capture_none   and piece is None)
                }

                # Include compound moves in move alternatives
                moves_alt |= moves_comp

            # Include move alteratives in main moves
            moves |= moves_alt

        # Apply special rules
        moves = self._legal_moves_special(moves, check_safe = check_safe)

        # Filter starting position
        moves -= {self.pos}

        return moves

    def _legal_moves_special(
            self,
            moves:      set[Pos],
            check_safe: bool = True,
        ) -> set[Pos]:
        other: Optional[Piece]

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
                # Test move
                test_state: Board = deepcopy(self.board)
                test_state.move_piece(self.pos, new_pos, check_safe = False)

                # Remove move if in check or anti-check
                if test_state.is_in_anti_check(self.owner) \
                or test_state.is_in_check(self.owner):
                    moves -= {new_pos}

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
    move_log: list[tuple[Pos, Pos]]

    def __init__(self, size_x: int = 8, size_y: int = 8) -> None:
        self.size_x: int = size_x
        self.size_y: int = size_y

        self.pieces   = {}
        self.move_log = []

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

        if n < 0:
            n = random.randrange(960)

        board = Board(8, 8)

        board.add_new_piece_row('Pawn', Player.WHITE, '2')

        pieces: list[Optional[str]] = 8*[None]

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

        if n <= 3:
            b = 0
        elif n <= 6:
            b = 1
        elif n <= 8:
            b = 2
        else:
            b = 3
        n //= b+1

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

    def piece_at(self, pos: Pos) -> Optional[Piece]:
        return self.pieces.get(pos, None)

    def relocate_piece(self, piece: Piece, pos: Pos):
        self.remove_piece(piece)
        piece.pos = pos
        self.pieces[piece.pos] = piece

    def add_new_piece(self, name: str, owner: Player, pos: Pos) -> None:
        new_piece: Piece = Piece(name, owner, pos, self)
        self.pieces[pos] = new_piece

    def add_new_piece_row(self, names: str | list[Optional[str]], owner: Player, row: int|str) -> None:
        y: int = row if isinstance(row, int) else int(row)-1

        for x in range(self.size_x):
            if isinstance(names, str):
                self.add_new_piece(names, owner, Pos(x, y))
            elif isinstance(names, list):
                name: Optional[str] = names[x]
                if name is not None:
                    self.add_new_piece(name, owner, Pos(x, y))

    def remove_piece(self, piece: Piece):
        del self.pieces[piece.pos]

    def remove_piece_at(self, pos: Pos):
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
            new_piece: Optional[Piece] = self.piece_at(pos)
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
        piece: Optional[Piece] = self.piece_at(pos1)
        if piece is None:
            raise ValueError(f'There is no piece at {pos1}.')
        else:
            piece.move(pos2, info = info, check_safe = check_safe)

        self.move_log.append((pos1, pos2))

    def is_pos_within_board(self, pos: Pos):
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

    def winner(self) -> Optional[Player]:
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

    def all_legal_moves(self, filter_player: Optional[Player] = None) -> dict[Pos, set[Pos]]:
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

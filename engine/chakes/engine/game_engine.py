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


print('Hello Chakes!')


def pos_to_str(x: int, y: int) -> str:
    return chr(ord('a')+x) + str(y+1)


def poses_to_str(lst: set[tuple[int, int]]) -> set[str]:
    return set(map(lambda pos: pos_to_str(pos[0], pos[1]), lst))


def str_to_pos(pos: str) -> tuple[int, int]:
    x: int = ord(pos[0]) - ord('a')
    y: int = int(pos[1:]) - 1
    return x, y


class Player(Enum):
    WHITE = auto()
    BLACK = auto()

    def other(self) -> Player:
        if self == Player.WHITE:
            return Player.BLACK
        elif self == Player.BLACK:
            return Player.WHITE


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
    'Amazon':        (3, 'n*,1/2'),
    'Anti-King':     (3, 'f1*'),
    'Berolina Pawn': (3, 'o1X>,io2X>,c1>'),
    'Camel':         (3, '1/3'),
    'Chameleon':     (3, '1/2'),
    'Ferz':          (3, '1X'),
    'Grasshopper':   (3, '^n*'),
    'Man':           (3, '1*'),
    'Nightrider':    (3, 'n(1/2)'),
    'Wazir':         (3, '1+'),
}


class Piece:
    def __init__(
        self, name: str, owner: Player, pos_x: int, pos_y: int, game_state: GameState
    ) -> None:
        self.name:       str       = name
        self.owner:      Player    = owner
        self.pos_x:      int       = pos_x
        self.pos_y:      int       = pos_y
        self.game_state: GameState = game_state

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

    def _is_capture_move(self, pos_x: int, pos_y: int) -> bool:
        piece: Optional[Piece] = self.game_state.board[pos_x][pos_y]
        if piece is None:
            return False
        else:
            return piece.owner != self.owner

    def _legal_moves_in_direction(
        self,
        start_x:   int,
        start_y:   int,
        diff_x:    int,
        diff_y:    int,
        num_steps: int,
        leaps:     bool,
        hops:      bool,
    ) -> set[tuple[int, int]]:
        if num_steps == 0:
            return set()

        new_x: int = start_x + diff_x
        new_y: int = start_y + diff_y

        if not self.game_state.is_pos_within_board(new_x, new_y):
            return set()

        new_piece: Optional[Piece] = self.game_state.board[new_x][new_y]

        if hops:
            if new_piece is not None:
                return self._legal_moves_in_direction(new_x, new_y, diff_x, diff_y, 1, leaps, False)
            else:
                return self._legal_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1, leaps, True)

        # If square occupied
        if new_piece is not None:
            ret: set[tuple[int, int]] = set()

            if new_piece.owner != self.owner:
                ret |= {(new_x, new_y)}

            if leaps:
                ret |= self._legal_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1, leaps, hops)

            return ret

        # If square unoccupied
        else:
            if num_steps > 1:
                return self._legal_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1, leaps, hops)
            else:
                return {(new_x, new_y)} | self._legal_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1, leaps, hops)

    def move(
            self,
            new_pos_x:   int,
            new_pos_y:   int,
            info:        str = '',
            check_safe:  bool = True
        ) -> None:
        if (new_pos_x, new_pos_y) not in self.legal_moves(check_safe = check_safe):
            raise ValueError(f'{self.name} can not move from {pos_to_str(self.pos_x, self.pos_y)} to {pos_to_str(new_pos_x, new_pos_y)}.')

        if check_safe and (cooldown := self.get_cooldown()) != 0.0:
            raise ValueError(f'Cooldown for {self.name} at {pos_to_str(self.pos_x, self.pos_y)} is {cooldown}')

        self._move_special(new_pos_x, new_pos_y, info = info)

        self.game_state.board[new_pos_x][new_pos_y]   = self
        self.game_state.board[self.pos_x][self.pos_y] = None

        self.pos_x = new_pos_x
        self.pos_y = new_pos_y

        self.has_moved      = True
        self.last_move_time = monotonic()

    def _move_special(
            self,
            new_pos_x: int,
            new_pos_y: int,
            info:      str = ''
        ) -> None:
        other: Optional[Piece]

        match self.name:
            case 'Pawn':
                # Mark en passantable
                if abs(self.pos_y - new_pos_y) == 2:
                    self._en_passantable = True
                else:
                    self._en_passantable = False

                # Perform en passant
                if self.pos_x != new_pos_x:
                    other = self.game_state.board[new_pos_x][self.pos_y]
                    if other is not None:
                        if getattr(other, '_en_passantable', False):
                            self.game_state.board[new_pos_x][self.pos_y] = None

            case 'King':
                # Castling
                if abs(new_pos_x - self.pos_x) == 2:
                    diff_x: int = (new_pos_x - self.pos_x) // abs(new_pos_x - self.pos_x)
                    cur_x:  int = self.pos_x + diff_x
                    while self.game_state.is_pos_within_board(cur_x, self.pos_y):
                        other = self.game_state.board[cur_x][self.pos_y]
                        if other is not None:
                            if other.name == "Rook":
                                self.game_state.board[cur_x][self.pos_y] = None
                                self.game_state.board[self.pos_x+diff_x][self.pos_y] = other
                                other.pos_x = self.pos_x+diff_x
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
            if new_pos_y == 0 or new_pos_y == self.game_state.size_y-1:
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
        ) -> set[tuple[int, int]]:
        """
        Returns a set of legal moves for a piece.

        Args:
            check_safe:      Whether to exclude moves that are unsafe
            invert_captures: Whether to invert capturing and non-capturing moves

        Returns:
            Set of legal moves
        """

        moves: set[tuple[int, int]] = set()

        for pattern in self.moveset.split(','):
            moves_temp: set[tuple[int, int]] = set()
            match: Optional[re.Match] = None

            num_steps_start: int
            num_steps_end:   int

            must_capture:     bool = False
            must_not_capture: bool = False
            captures_friends: bool = False
            leaps:            bool = False
            hops:             bool = False
            unsafe:           bool = False

            # Parse condtions
            while True:
                match pattern[0]:
                    # Must capture friend
                    case 'f':
                        self.owner = self.owner.other()
                        captures_friends = True

                        pattern = pattern[1:]
                    # Must be initial move
                    case 'i':
                        pattern = pattern[1:] if not self.has_moved else '_'

                    # Must not capture
                    case 'o':
                        if not invert_captures:
                            must_not_capture = True
                        else:
                            must_capture = True
                        pattern = pattern[1:]

                    # Must capture enemy
                    case 'c':
                        if not invert_captures:
                            must_capture = True
                        else:
                            must_not_capture = True
                        pattern = pattern[1:]

                    # No more conditions
                    case _:
                        break

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
                if pattern[0] == 'n':
                    num_steps_start = num_steps_end = -1
                    pattern = pattern[1:]
                elif match := re.match(r'[0-9]+\-[0-9]+', pattern):
                    num_steps_start, num_steps_end = \
                        tuple([int(num) for num in pattern[:match.end()].split('-')[:2]][:2])
                    if num_steps_start >= num_steps_end:
                        raise AssertionError(f'For number of steps range in {self.name}, {num_steps_start} is larger than or equal to {num_steps_end}.')
                    pattern = pattern[match.end():]
                elif match := re.match(r'[0-9]+', pattern):
                    num_steps_start = num_steps_end = int(pattern[:match.end()])
                    pattern = pattern[match.end():]
            else:
                num_steps_start = num_steps_end = 1

            # Parse parentheses
            if match := re.match(r'\(.*\)', pattern):
                pattern = pattern[1:match.end()-1] + pattern[match.end():]

            # Parse direction
            if match := re.match(r'X>|X<|<>|>=|<=|>|<|=|\+|X|\*|[0-9]+/[0-9]+', pattern):
                move_type: str = pattern[:match.end()]
                pattern = pattern[match.end():]

                # For each number of steps
                for num_steps in range(num_steps_start, num_steps_end+1):
                    match move_type:

                        # Orthogonally forwards
                        case '>':
                            moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, 0, self._forwards(), num_steps, leaps, hops)

                        # Orthogonally backwards
                        case '<':
                            moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, 0, -self._forwards(), num_steps, leaps, hops)

                        # Orthogonally forwards and backwards
                        case '<>':
                            for direction in (-1, 1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, 0, direction, num_steps, leaps, hops)

                        # Orthogonally sideways
                        case '=':
                            for direction in (-1, 1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, direction, 0, num_steps, leaps, hops)

                        # Orthogonally forwards and sideways
                        case '>=':
                            moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, 0, self._forwards(), num_steps, leaps, hops)
                            for direction in (-1, 1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, direction, 0, num_steps, leaps, hops)

                        # Orthogonally backwards and sideways
                        case '<=':
                            moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, 0, -num_steps, 1, leaps, hops)
                            for direction in (-1, 1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, direction*self._forwards(), 0, num_steps, leaps, hops)

                        # Diagonally forwards
                        case 'X>':
                            y = self._forwards()
                            for x in -1, 1:
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps, leaps, hops)

                        # Diagonally backwards
                        case 'X<':
                            y = -self._forwards()
                            for x in -1, 1:
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps, leaps, hops)

                        # Orthogonally
                        case '+':
                            for x, y in (1, 0), (0, 1), (-1, 0), (0, -1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps, leaps, hops)

                        # Diagonally
                        case 'X':
                            for x, y in (1, 1), (-1, 1), (1, -1), (-1, -1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps, leaps, hops)

                        # Any direction
                        case '*':
                            for x, y in (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1):
                                moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps, leaps, hops)

                        # Hippogonally
                        case _ if '/' in move_type:
                            a: int
                            b: int
                            a, b = tuple([int(num_str) for num_str in move_type.split('/')][:2])
                            for c, d in [(a, b), (-a, b), (a, -b), (-a, -b)]:
                                for x, y in [(c, d), (d, c)]:
                                    moves_temp |= self._legal_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps, leaps, hops)

            # Filter captures if 'c' was specified
            if must_capture:
                moves_temp = set(filter(lambda pos: self._is_capture_move(pos[0], pos[1]), moves_temp))

            # Filter non-captures if 'o' was specified
            if must_not_capture:
                moves_temp = set(filter(lambda pos: not self._is_capture_move(pos[0], pos[1]), moves_temp))

            # Restore owner if needed
            if captures_friends:
                self.owner = self.owner.other()

            # Append temporary moves to main moves
            moves |= moves_temp

        # Apply special rules
        moves = self._legal_moves_special(moves, check_safe = check_safe)

        return moves

    def _legal_moves_special(
            self,
            moves:      set[tuple[int, int]],
            check_safe: bool = True,
        ) -> set[tuple[int, int]]:
        other: Optional[Piece]

        match self.name:
            case 'Pawn':
                # En passant
                for x, y in (self.pos_x-1, self.pos_y), (self.pos_x+1, self.pos_y):
                    if self.game_state.is_pos_within_board(x, y):
                        other = self.game_state.board[x][y]
                        if other is not None:
                            if getattr(other, '_en_passantable', False) \
                            and other.owner != self.owner \
                            and other.get_cooldown() > 0:
                                moves |= {(x, y+self._forwards())}

            case 'King':
                # Castling
                attacked:     set[tuple[int, int]] = self.game_state.attacked_squares(self.owner, invert_captures = False) if check_safe else set()
                attacked_inv: set[tuple[int, int]] = self.game_state.attacked_squares(self.owner, invert_captures = True) if check_safe else set()
                for diff_x in (-1, 1):
                    if  (self.pos_x,          self.pos_y) not in attacked \
                    and (self.pos_x + diff_x, self.pos_y) not in attacked_inv:
                        cur_x: int = self.pos_x + diff_x
                        while self.game_state.is_pos_within_board(cur_x, self.pos_y):
                            other = self.game_state.board[cur_x][self.pos_y]
                            if other is not None:
                                if other.name == 'Rook' \
                                and other.owner == self.owner \
                                and not self.has_moved \
                                and not other.has_moved \
                                and self.game_state.is_pos_within_board(self.pos_x+2*diff_x, self.pos_y) \
                                and self.game_state.board[self.pos_x+2*diff_x][self.pos_y] is None:
                                    moves |= {(self.pos_x+2*diff_x, self.pos_y)}
                                break
                            cur_x += diff_x

        # Filter unsafe moves
        if check_safe:
            for new_x, new_y in set(moves):
                test_state: GameState = deepcopy(self.game_state)
                test_state.move_piece(self.pos_x, self.pos_y, new_x, new_y, check_safe = False)
                attacked_anti_kings: set[Piece] = set()
                all_anti_kings:      set[Piece] = set([
                    piece
                    for pieces in test_state.board
                    for piece  in pieces
                        if  piece is not None
                        and piece.owner == self.owner
                        and piece.name == 'Anti-King'
                ])
                for att_x, att_y in test_state.attacked_squares(self.owner):
                    piece: Optional[Piece] = test_state.board[att_x][att_y]
                    if piece is not None:
                        if piece.owner == self.owner:
                            match piece.name:
                                case 'King':
                                    moves -= {(new_x, new_y)}
                                case 'Anti-King':
                                    attacked_anti_kings |= {piece}

                # Remove move if any Anti-King is unattacked
                if all_anti_kings != attacked_anti_kings:
                    moves -= {(new_x, new_y)}

        # Filter moves that capture invinsible pieces
        if check_safe:
            for pos_x, pos_y in set(moves):
                other = self.game_state.board[pos_x][pos_y]
                if other is not None:
                    if other.name == 'King' \
                    or other.name == 'Anti-King':
                        moves -= {(pos_x, pos_y)}

        return moves


class GameState:
    pieces:   list[Piece]                                   = []
    move_log: list[tuple[tuple[int, int], tuple[int, int]]] = []

    def __init__(self, size_x: int = 8, size_y: int = 8) -> None:
        self.size_x: int = size_x
        self.size_y: int = size_y

        # Define empty size_x*size_y board
        self.board: list[list[Optional[Piece]]] = [
            [None for _ in range(size_x)] for _ in range(size_y)
        ]

    @staticmethod
    def default() -> GameState:
        state = GameState(8, 8)

        state.add_piece_row('Pawn', Player.WHITE, '2')

        state.add_piece_str('Rook',   Player.WHITE, 'a1')
        state.add_piece_str('Knight', Player.WHITE, 'b1')
        state.add_piece_str('Bishop', Player.WHITE, 'c1')
        state.add_piece_str('Queen',  Player.WHITE, 'd1')
        state.add_piece_str('King',   Player.WHITE, 'e1')
        state.add_piece_str('Bishop', Player.WHITE, 'f1')
        state.add_piece_str('Knight', Player.WHITE, 'g1')
        state.add_piece_str('Rook',   Player.WHITE, 'h1')

        state.symmetry()

        return state

    @staticmethod
    def berolina_chess() -> GameState:
        state = GameState(8, 8)

        state.add_piece_row('Berolina Pawn', Player.WHITE, '2')

        state.add_piece_str('Rook',   Player.WHITE, 'a1')
        state.add_piece_str('Knight', Player.WHITE, 'b1')
        state.add_piece_str('Bishop', Player.WHITE, 'c1')
        state.add_piece_str('Queen',  Player.WHITE, 'd1')
        state.add_piece_str('King',   Player.WHITE, 'e1')
        state.add_piece_str('Bishop', Player.WHITE, 'f1')
        state.add_piece_str('Knight', Player.WHITE, 'g1')
        state.add_piece_str('Rook',   Player.WHITE, 'h1')

        state.symmetry()

        return state


    @staticmethod
    def anti_king_chess() -> GameState:
        state = GameState.default()

        state.add_piece_str('Anti-King', Player.WHITE, 'd6')
        state.add_piece_str('Anti-King', Player.BLACK, 'd3')

        return state

    @staticmethod
    def chess960() -> GameState:
        state = GameState(8, 8)

        state.add_piece_row('Pawn', Player.WHITE, '2')

        pieces: list[str] = \
            2*['Rook'] + \
            2*["Knight"] + \
            2*["Bishop"] + \
            ["Queen"] + \
            ["King"]

        # Randomize until order is valid
        while True:
            order: list[str] = ['Rook', 'King', 'Rook']
            random.shuffle(pieces)
            for piece in pieces:
                if piece == order[0]:
                    del order[0]
                if len(order) == 0:
                    break

            if len(order) == 0:
                break

        # Add first row
        for i, piece in enumerate(pieces):
            state.add_piece(piece, Player.WHITE, i, 0)

        state.symmetry()

        return state

    def piece_at(self, pos: str) -> Optional[Piece]:
        x, y = str_to_pos(pos)
        return self.board[x][y]

    def add_piece(self, name: str, owner: Player, pos_x: int, pos_y: int) -> None:
        new_piece: Piece = Piece(name, owner, pos_x, pos_y, self)
        self.pieces.append(new_piece)
        self.board[pos_x][pos_y] = new_piece

    def add_piece_str(self, name: str, owner: Player, pos: str) -> None:
        x, y = str_to_pos(pos)
        self.add_piece(name, owner, x, y)

    def add_piece_row(self, name: str, owner: Player, row: int|str) -> None:
        y: int = row if isinstance(row, int) else int(row)-1

        for x in range(self.size_x):
            self.add_piece(name, owner, x, y)

    def remove_piece(self, pos_x: int, pos_y: int):
        self.board[pos_x][pos_y] = None

    def remove_piece_str(self, pos: str) -> None:
        x, y = str_to_pos(pos)
        self.remove_piece(x, y)

    def upside_down(self) -> None:
        for y1 in range(self.size_y // 2):
            for x in range(self.size_x):
                y2: int = self.size_y-1 - y1
                piece1: Optional[Piece] = self.board[x][y1]
                piece2: Optional[Piece] = self.board[x][y2]
                self.board[x][y1], self.board[x][y2] = self.board[x][y2], self.board[x][y1]
                if piece1 is not None:
                    piece1.pos_y = y2
                if piece2 is not None:
                    piece2.pos_y = y1

    def symmetry(self) -> None:
        for piece in [piece for pieces in self.board for piece in pieces]:
            if piece is not None:
                x: int = piece.pos_x
                y: int = self.size_y-1 - piece.pos_y
                new_piece: Optional[Piece] = self.board[x][y]
                if new_piece is not None:
                    raise RuntimeError(f'Impossible to make symmetry due to {piece.name} at {pos_to_str(piece.pos_x, piece.pos_y)} and {new_piece.name} at {pos_to_str(x, y)}.')
                self.add_piece(piece.name, piece.owner.other(), x, y)

    def move_piece(
            self,
            pos_x1:     int,
            pos_y1:     int,
            pos_x2:     int,
            pos_y2:     int,
            info:       str  = '',
            check_safe: bool = True,
        ) -> None:
        piece: Optional[Piece] = self.board[pos_x1][pos_y1]

        if piece is None:
            raise ValueError(f'There is no piece at {pos_to_str(pos_x1, pos_y1)}.')
        else:
            piece.move(pos_x2, pos_y2, info = info, check_safe = check_safe)

        self.move_log.append(((pos_x1, pos_y1), (pos_x2, pos_y2)))

    def move_piece_str(self, pos1: str, pos2: str, info: str = '') -> None:
        x1, y1 = str_to_pos(pos1)
        x2, y2 = str_to_pos(pos2)
        self.move_piece(x1, y1, x2, y2, info = info)

    def move_log_str(self):
        return list(map(lambda move: (pos_to_str(move[0][0], move[0][1]), pos_to_str(move[1][0], move[1][1])), self.move_log))

    def is_pos_within_board(self, x: int, y: int):
        return \
            x >= 0 and \
            y >= 0 and \
            x < self.size_x and \
            y < self.size_y

    def attacked_squares(
            self,
            player:          Player,
            invert_captures: bool = False
        ) -> set[tuple[int, int]]:
        squares: set[tuple[int, int]] = set()

        for pieces in self.board:
            for piece in pieces:
                if piece is not None:
                    if piece.owner == player.other():
                        squares |= piece.legal_moves(check_safe = False, invert_captures = invert_captures)

        return squares

    def winner(self) -> Optional[Player]:
        can_move_by_player: dict[Player, bool] = {
            Player.WHITE: False,
            Player.BLACK: False,
        }
        for pieces in self.board:
            for piece in pieces:
                if piece is not None:
                    if piece.legal_moves() != set():
                        can_move_by_player[piece.owner] = True

        for player, can_move in can_move_by_player.items():
            if not can_move:
                return player.other()

        return None


    def __str__(self) -> str:
        ret: str = ''
        for y in reversed(range(self.size_y)):
            ret += f'\033[33m{pos_to_str(0, y)[1:]} \033[0m'
            for x in range(self.size_x):
                piece = self.board[x][y]
                ret += '.' if piece is None else str(piece)
                ret += ' ' if x < self.size_x else ''
            ret += '\n'
        ret = ret[:-1]
        ret += '\n  '
        ret += ' '.join([f'\033[33m{pos_to_str(x, 0)[0]}' for x in range(self.size_x)])
        ret += '\033[0m'
        return ret

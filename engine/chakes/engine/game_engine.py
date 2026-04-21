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

from enum import auto, Enum
import re
from time import monotonic, sleep
from typing import Optional, Tuple


print('Hello Chakes!')


def pos_to_str(x: int, y: int) -> str:
    return chr(ord('A')+x) + str(y+1)


def pos_list_to_str(lst: list[Tuple[int, int]]) -> list[str]:
    return list(map(lambda pos: pos_to_str(pos[0], pos[1]), lst))


def str_to_pos(pos: str) -> Tuple[int, int]:
    x: int = ord(pos[0]) - ord('A')
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
piece_defs = {
    'Pawn':   (1, 'o1>,io2>,c1X>'),
    'Rook':   (5, 'n+'),
    'Knight': (3, '~1/2'),
    'Bishop': (3, 'nX'),
    'Queen':  (9, 'n*'),
    'King':   (3, '1*'),
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

    def _valid_moves_in_direction(
        self,
        start_x:   int,
        start_y:   int,
        diff_x:    int,
        diff_y:    int,
        num_steps: int,
        hops:      bool = False,
        captures:  bool = True,
    ) -> list[Tuple[int, int]]:
        if num_steps == 0:
            return []

        new_x: int = start_x + diff_x
        new_y: int = start_y + diff_y

        if not self.game_state.is_pos_within_board(new_x, new_y):
            return []

        new_piece: Optional[Piece] = self.game_state.board[new_x][new_y]
        if new_piece is not None:
            ret: list[Tuple[int, int]] = []

            if captures:
                if new_piece.owner != self.owner:
                    ret += [(new_x, new_y)]

            if hops or not captures:
                ret += self._valid_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1)

            return ret
        else:
            if num_steps > 1:
                return self._valid_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1)
            else:
                return [(new_x, new_y)] + self._valid_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1)

    def move(self, new_pos_x: int, new_pos_y: int) -> None:
        if (new_pos_x, new_pos_y) not in self.valid_moves():
            raise ValueError(f'{self.name} can not move from {pos_to_str(self.pos_x, self.pos_y)} to {pos_to_str(new_pos_x, new_pos_y)}.')

        if (cooldown := self.get_cooldown()) != 0.0:
            raise ValueError(f'Cooldown for {self.name} at {pos_to_str(self.pos_x, self.pos_y)} is {cooldown}')

        self._move_special(new_pos_x, new_pos_y)

        self.game_state.board[new_pos_x][new_pos_y]   = self
        self.game_state.board[self.pos_x][self.pos_y] = None

        self.pos_x = new_pos_x
        self.pos_y = new_pos_y

        self.has_moved      = True
        self.last_move_time = monotonic()

    def _move_special(self, new_pos_x: int, new_pos_y: int) -> None:
        other: Optional[Piece]

        match self.name:
            case 'Pawn':
                # Mark en passentable
                if abs(self.pos_y - new_pos_y) == 2:
                    self._enpassantable = True # type: ignore
                else:
                    self._enpassantable = False # type: ignore

                # Perform en passent
                if self.pos_x != new_pos_x \
                and self.game_state.board[new_pos_x][new_pos_y] is None:
                    self.game_state.board[new_pos_x][self.pos_y] = None

                # Promote
                if new_pos_y == 0 or new_pos_y == self.game_state.size_y-1:
                    self.name = 'Queen'

                    # TODO: Allow promotion to other pieces

                    self.value   = piece_defs[self.name][0]
                    self.moveset = piece_defs[self.name][1]

            case 'King':
                # Castling
                # TODO: King should be captured if castling square is captured before cooldown
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
                                return
                        cur_x += diff_x

    def get_cooldown(self) -> float:
        cooldown: float = self.last_move_time - monotonic() + self.value
        return max(cooldown, 0.0)

    def valid_moves(self) -> list[Tuple[int, int]]:
        move_list: list[Tuple[int, int]] = []
        for pattern in self.moveset.split(','):
            move_list_temp: list[Tuple[int, int]] = []
            match: Optional[re.Match] = None

            num_steps_start: int
            num_steps_end:   int

            must_capture:     bool = False
            must_not_capture: bool = False
            hops:             bool = False

            # Parse condtions
            if pattern[0] == 'i': # Can only move if first move
                if self.has_moved:
                    continue
                pattern = pattern[1:]
            if pattern[0] == 'o': # Can only move if not capturing
                must_not_capture = True
                pattern = pattern[1:]
            if pattern[0] == 'c': # Can only move if capturing
                must_capture = True
                pattern = pattern[1:]

            # Parse move type
            if pattern[0] == '~':
                hops = True
                pattern = pattern[1:]

            # Parse number of steps
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

            # Parse direction
            if match := re.match(r'X>|X<|<>|>=|<=|>|<|=|\+|X|\*|/', pattern):
                move_type: str = pattern[:match.end()]
                pattern = pattern[match.end():]

                # For each number of steps
                for num_steps in range(num_steps_start, num_steps_end+1):
                    # Orthogonally forwards
                    if move_type == '>':
                        move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, 0, self._forwards(), num_steps)

                    # Orthogonally backwards
                    if move_type == '<':
                        move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, 0, -self._forwards(), num_steps)

                    # Orthogonally forwards and backwards
                    if move_type == '<>':
                        for direction in (-1, 1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, 0, direction, num_steps)

                    # Orthogonally sideways
                    if move_type == '=':
                        for direction in (-1, 1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, direction, 0, num_steps)

                    # Orthogonally forwards and sideways
                    if move_type == '>=':
                        move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, 0, self._forwards(), num_steps)
                        for direction in (-1, 1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, direction, 0, num_steps)

                    # Orthogonally backwards and sideways
                    if move_type == '<=':
                        move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, 0, -num_steps, 1)
                        for direction in (-1, 1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, direction*self._forwards(), 0, num_steps)

                    # Diagonally forwards
                    if move_type == 'X>':
                        y = self._forwards()
                        for x in -1, 1:
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps)

                    # Diagonally backwards
                    if move_type == 'X<':
                        y = -self._forwards()
                        for x in -1, 1:
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps)

                    # Orthogonally
                    if move_type == '+':
                        for x, y in (1, 0), (0, 1), (-1, 0), (0, -1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps)

                    # Diagonally
                    if move_type == 'X':
                        for x, y in (1, 1), (-1, 1), (1, -1), (-1, -1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps)

                    # Any direction
                    if move_type == '*':
                        for x, y in (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1):
                            move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps)

                    # Hippogonally
                    if move_type == '/':
                        if match := re.match(r'[0-9]+', pattern):
                            a: int = num_steps
                            b: int = int(pattern[:match.end()])
                            pattern = pattern[:match.end()]
                            for c, d in [(a, b), (-a, b), (a, -b), (-a, -b)]:
                                for x, y in [(c, d), (d, c)]:
                                    move_list_temp += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, 1)
                            pattern = pattern[match.end():]

            # Filter captures if 'c' was specified
            if must_capture:
                move_list_temp = list(filter(lambda pos: self._is_capture_move(pos[0], pos[1]), move_list_temp))

            # Filter non-captures if 'i' was specified
            if must_not_capture:
                move_list_temp = list(filter(lambda pos: not self._is_capture_move(pos[0], pos[1]), move_list_temp))

            # Append temporary move list to main move list
            move_list += move_list_temp

        # Add special moves
        move_list += self._valid_moves_special()

        # Return unique moves in move_list
        return list(set(move_list))

    def _valid_moves_special(self) -> list[Tuple[int, int]]:
        move_list: list[Tuple[int, int]] = []
        other: Optional[Piece]

        match self.name:
            case 'Pawn':
                # En passant
                for x, y in (self.pos_x-1, self.pos_y), (self.pos_x+1, self.pos_y):
                    if self.game_state.is_pos_within_board(x, y):
                        other = self.game_state.board[x][y]
                        if other is not None:
                            if getattr(other, '_enpassantable', False) \
                            and other.owner != self.owner \
                            and other.get_cooldown() > 0:
                                move_list.append((x, y+self._forwards()))

            case 'King':
                # Castling
                for diff_x in (-1, 1):
                    cur_x: int = self.pos_x + diff_x
                    while self.game_state.is_pos_within_board(cur_x, self.pos_y):
                        other = self.game_state.board[cur_x][self.pos_y]
                        if other is not None:
                            if other.name == 'Rook' \
                            and other.owner == self.owner \
                            and not self.has_moved \
                            and not other.has_moved \
                            and self.game_state.is_pos_within_board(self.pos_x-2*diff_x, self.pos_y) \
                            and self.game_state.board[self.pos_x-2*diff_x][self.pos_y] is None:
                                move_list.append((self.pos_x-2*diff_x, self.pos_y))
                            break
                        cur_x += diff_x

        return move_list


class GameState:
    pieces: list[Piece] = []

    @staticmethod
    def default():
        state = GameState(8, 8)

        state.add_piece('Pawn', Player.WHITE, 0, 1)
        state.add_piece('Pawn', Player.WHITE, 1, 1)
        state.add_piece('Pawn', Player.WHITE, 2, 1)
        state.add_piece('Pawn', Player.WHITE, 3, 1)
        state.add_piece('Pawn', Player.WHITE, 4, 1)
        state.add_piece('Pawn', Player.WHITE, 5, 1)
        state.add_piece('Pawn', Player.WHITE, 6, 1)
        state.add_piece('Pawn', Player.WHITE, 7, 1)

        state.add_piece('Pawn', Player.BLACK, 0, 6)
        state.add_piece('Pawn', Player.BLACK, 1, 6)
        state.add_piece('Pawn', Player.BLACK, 2, 6)
        state.add_piece('Pawn', Player.BLACK, 3, 6)
        state.add_piece('Pawn', Player.BLACK, 4, 6)
        state.add_piece('Pawn', Player.BLACK, 5, 6)
        state.add_piece('Pawn', Player.BLACK, 6, 6)
        state.add_piece('Pawn', Player.BLACK, 7, 6)

        state.add_piece('Rook', Player.WHITE, 0, 0)
        state.add_piece('Knight', Player.WHITE, 1, 0)
        state.add_piece('Bishop', Player.WHITE, 2, 0)
        state.add_piece('Queen', Player.WHITE, 3, 0)
        state.add_piece('King', Player.WHITE, 4, 0)
        state.add_piece('Bishop', Player.WHITE, 5, 0)
        state.add_piece('Knight', Player.WHITE, 6, 0)
        state.add_piece('Rook', Player.WHITE, 7, 0)

        state.add_piece('Rook', Player.BLACK, 0, 7)
        state.add_piece('Knight', Player.BLACK, 1, 7)
        state.add_piece('Bishop', Player.BLACK, 2, 7)
        state.add_piece('Queen', Player.BLACK, 3, 7)
        state.add_piece('King', Player.BLACK, 4, 7)
        state.add_piece('Bishop', Player.BLACK, 5, 7)
        state.add_piece('Knight', Player.BLACK, 6, 7)
        state.add_piece('Rook', Player.BLACK, 7, 7)

        return state

    def __init__(self, size_x: int = 8, size_y: int = 8) -> None:
        self.size_x: int = size_x
        self.size_y: int = size_y

        # Define empty size_x*size_y board
        self.board: list[list[Optional[Piece]]] = [
            [None for _ in range(size_x)] for _ in range(size_y)
        ]

    def piece_at(self, pos: str) -> Optional[Piece]:
        x, y = str_to_pos(pos)
        return self.board[x][y]

    def add_piece(self, name: str, owner: Player, pos_x: int, pos_y: int) -> None:
        new_piece: Piece = Piece(name, owner, pos_x, pos_y, self)
        self.pieces.append(new_piece)
        self.board[pos_x][pos_y] = new_piece

    def move_piece(self, pos_x1: int, pos_y1: int, pos_x2: int, pos_y2: int) -> None:
        piece: Optional[Piece] = self.board[pos_x1][pos_y1]

        if piece is None:
            raise ValueError(f'There is no piece at {pos_to_str(pos_x1, pos_y1)}.')
        else:
            piece.move(pos_x2, pos_y2)

    def move_piece_str(self, pos1: str, pos2: str) -> None:
        x1, y1 = str_to_pos(pos1)
        x2, y2 = str_to_pos(pos2)
        self.move_piece(x1, y1, x2, y2)

    def is_pos_within_board(self, x: int, y: int):
        return \
            x >= 0 and \
            y >= 0 and \
            x < self.size_x and \
            y < self.size_y

    def __str__(self) -> str:
        ret: str = ''
        for y in reversed(range(self.size_y)):
            ret += f'\033[33m{pos_to_str(0, y)[1:]} \033[0m'
            for x in range(self.size_x):
                piece = self.board[x][y]
                ret += '∘' if piece is None else str(piece)
                ret += ' ' if x < self.size_x else ''
            ret += '\n'
        ret = ret[:-1]
        ret += '\n  '
        ret += ' '.join([f'\033[33m{pos_to_str(x, 0)[0]}' for x in range(self.size_x)])
        ret += '\033[0m'
        return ret

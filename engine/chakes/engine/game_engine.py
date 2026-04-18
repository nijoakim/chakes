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

from enum import Enum
import re
from time import monotonic
from typing import Optional, Tuple

print("Hello Chakes!")


class Player(Enum):
    WHITE = 0
    BLACK = 1


# Parlett's movement notation
# Format: name: (value, movement)
piece_defs = {
    "Pawn":   (1, "o1>,io2>,c1X>"),
    "Rook":   (5, "+n"),
    "Knight": (3, "~1/2"),
    "Bishop": (3, "Xn"),
    "Queen":  (9, "*n"),
    "King":   (3, "+n"),
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
        self.last_move_time: float = -float("inf")

        # Piece definition
        self.value:   int = piece_defs[name][0]
        self.moveset: str = piece_defs[name][1]

    def __str__(self) -> str:
        return self.name[0] if self.name != "Knight" else "N"

    def _valid_moves_in_direction(self, start_x: int, start_y: int, diff_x: int, diff_y: int, num_steps: int) -> list[Tuple[int, int]]:
        if num_steps == 0:
            return []

        new_x: int = start_x + diff_x
        new_y: int = start_y + diff_y
        if not self.game_state.is_pos_within_board(new_x, new_y):
            return []
        else:
            return [(new_x, new_y)] + self._valid_moves_in_direction(new_x, new_y, diff_x, diff_y, num_steps-1)

    def move(self, new_pos_x: int, new_pos_y: int) -> None:
        # TODO: Verify that move is legal

        self.game_state.board[new_pos_x][new_pos_y]   = self
        self.game_state.board[self.pos_x][self.pos_y] = None

        self.pos_x = new_pos_x
        self.pos_y = new_pos_y

        self.has_moved      = True
        self.last_move_time = monotonic()

    def get_cooldown(self) -> float:
        cooldown: float = self.last_move_time - monotonic() + self.value
        return max(cooldown, 0.0)

    def valid_moves(self) -> list[Tuple[int, int]]:
        # TODO: Parse piece_movesets
        move_list: list[Tuple[int, int]] = []
        for pattern in self.moveset.split(","):
            match: Optional[re.Match] = None
            num_steps: int
            can_capture: bool = True

            # Parse condtions
            if pattern[0] == "i": # Can only move if first move
                if self.has_moved:
                    continue
                pattern = pattern[1:]
            if pattern[0] == "o": # Can only move if not capturing
                pattern = pattern[1:]
            if pattern[0] == "c": # Can only move if capturing
                pattern = pattern[1:]

            # Parse move type
            if pattern[0] in ["+", "X"]:
                move_type: str = pattern[0]
                pattern = pattern[1:]

                # Parse number of steps
                if pattern[0] == "n": # O
                    num_steps = -1
                    pattern = pattern[1:]
                elif match := re.match(r"[0-9]", pattern):
                    num_steps = int(pattern[:match.end()])
                    pattern = pattern[match.end():]

                if move_type == "+": # Orthogonal
                    for x, y in (1, 0), (0, 1), (-1, 0), (0, -1):
                        move_list += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num_steps)
            elif pattern[0] == "~":
                pattern = pattern[1:]

            # Parse hippogonal move
            if match := re.match(r"[0-9]+/[0-9]+", pattern):
                a, b = tuple([int(x) for x in pattern[:match.end()].split("/")][:2])
                for c, d in [(a, b), (-a, b), (a, -b), (-a, -b)]:
                    for x, y in [(c, d), (d, c)]:
                        move_list += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, 1)
                pattern = pattern[match.end():]

        return move_list


class GameState:
    pieces: list[Piece] = []

    @staticmethod
    def default():
        state = GameState(8, 8)

        state.add_piece("Pawn", Player.WHITE, 0, 1)
        state.add_piece("Pawn", Player.WHITE, 1, 1)
        state.add_piece("Pawn", Player.WHITE, 2, 1)
        state.add_piece("Pawn", Player.WHITE, 3, 1)
        state.add_piece("Pawn", Player.WHITE, 4, 1)
        state.add_piece("Pawn", Player.WHITE, 5, 1)
        state.add_piece("Pawn", Player.WHITE, 6, 1)
        state.add_piece("Pawn", Player.WHITE, 7, 1)

        state.add_piece("Pawn", Player.BLACK, 0, 6)
        state.add_piece("Pawn", Player.BLACK, 1, 6)
        state.add_piece("Pawn", Player.BLACK, 2, 6)
        state.add_piece("Pawn", Player.BLACK, 3, 6)
        state.add_piece("Pawn", Player.BLACK, 4, 6)
        state.add_piece("Pawn", Player.BLACK, 5, 6)
        state.add_piece("Pawn", Player.BLACK, 6, 6)
        state.add_piece("Pawn", Player.BLACK, 7, 6)

        state.add_piece("Rook", Player.WHITE, 0, 0)
        state.add_piece("Knight", Player.WHITE, 1, 0)
        state.add_piece("Bishop", Player.WHITE, 2, 0)
        state.add_piece("Queen", Player.WHITE, 3, 0)
        state.add_piece("King", Player.WHITE, 4, 0)
        state.add_piece("Bishop", Player.WHITE, 5, 0)
        state.add_piece("Knight", Player.WHITE, 6, 0)
        state.add_piece("Rook", Player.WHITE, 7, 0)

        state.add_piece("Rook", Player.BLACK, 0, 7)
        state.add_piece("Knight", Player.BLACK, 1, 7)
        state.add_piece("Bishop", Player.BLACK, 2, 7)
        state.add_piece("Queen", Player.BLACK, 3, 7)
        state.add_piece("King", Player.BLACK, 4, 7)
        state.add_piece("Bishop", Player.BLACK, 5, 7)
        state.add_piece("Knight", Player.BLACK, 6, 7)
        state.add_piece("Rook", Player.BLACK, 7, 7)

        return state

    def __init__(self, size_x: int = 8, size_y: int = 8) -> None:
        self.size_x: int = size_x
        self.size_y: int = size_y

        # Define empty size_x*size_y board
        self.board: list[list[Optional[Piece]]] = [
            [None for _ in range(size_x)] for _ in range(size_y)
        ]

    def add_piece(self, name: str, owner: Player, pos_x: int, pos_y: int) -> None:
        new_piece: Piece = Piece(name, owner, pos_x, pos_y, self)
        self.pieces.append(new_piece)
        self.board[pos_x][pos_y] = new_piece

    def move_piece(self, pos_x1: int, pos_y1: int, pos_x2: int, pos_y2: int) -> None:
        # TODO: Verify that move is legal

        piece: Optional[Piece] = self.board[pos_x1][pos_y1]

        if piece is not None:
            piece.move(pos_x2, pos_y2)

    def is_pos_within_board(self, x: int, y: int):
        return \
            x >= 0 and \
            y >= 0 and \
            x < self.size_x and \
            y < self.size_y

    def __str__(self):
        ret: str = ""
        for y in reversed(range(self.size_y)):
            for x in range(self.size_x):
                piece = self.board[x][y]
                ret += "∘" if piece is None else str(piece)
                ret += " " if x < self.size_x else ""
            ret += "\n"
        return ret[:-1]


game_state = GameState.default()

game_state.move_piece(0, 0, 2, 4)
print(game_state.board[1][0].valid_moves())
print(game_state.board[2][4].valid_moves())
print(game_state.board[2][4].get_cooldown())

print(game_state)

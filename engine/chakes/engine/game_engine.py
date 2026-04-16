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
from typing import Optional, Tuple

print("Hello Chakes!")


class Player(Enum):
    WHITE = 0
    BLACK = 1


# Parlett's movement notation
piece_movesets = {
    "Pawn": "o1>,io2>,c1X>",
    "Rook": "n+",
    "Knight": "~1/2",
    "Bishop": "nX",
    "Queen": "n*",
    "King": "n+",
}


class Piece:
    def __init__(
        self, name: str, owner: Player, pos_x: int, pos_y: int, game_state: GameState
    ) -> None:
        self.name = name
        self.owner = owner
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.game_state = game_state

    def __str__(self) -> str:
        return self.name[0] if self.name != "Knight" else "N"

    def _valid_moves_in_direction(self, start_x: int, start_y: int, diff_x: int, diff_y: int, num: int = -1) -> list[Tuple[int, int]]:
        if num == 0:
            return []

        new_x: int = start_x + diff_x
        new_y: int = start_y + diff_y
        if not self.game_state.is_pos_within_board(new_x, new_y):
            return []
        else:
            return [(new_x, new_y)] + self._valid_moves_in_direction(new_x, new_y, diff_x, diff_y, num=num-1)

    def valid_moves(self) -> list[Tuple[int, int]]:
        # TODO: Parse piece_movesets
        move_list: list[Tuple[int, int]] = []
        for pattern in piece_movesets[self.name].split(","):
            pattern = pattern[::-1]
            match: Optional[re.Match] = None

            # Hippogonal move
            if match := re.match(r"[0-9]+/[0-9]+", pattern):
                a, b = tuple([int(x[::-1]) for x in pattern[:match.end()].split("/")][:2])
                for c, d in [(a, b), (-a, b), (a, -b), (-a, -b)]:
                    for x, y in [(c, d), (d, c)]:
                        move_list += self._valid_moves_in_direction(self.pos_x, self.pos_y, x, y, num=1)

        return move_list


class GameState:
    pieces: list[Piece] = []

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

        self.board[pos_x2][pos_y2] = self.board[pos_x1][pos_y1]
        self.board[pos_x1][pos_y1] = None

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


game_state = GameState(8, 8)

game_state.add_piece("Pawn", Player.WHITE, 0, 1)
game_state.add_piece("Pawn", Player.WHITE, 1, 1)
game_state.add_piece("Pawn", Player.WHITE, 2, 1)
game_state.add_piece("Pawn", Player.WHITE, 3, 1)
game_state.add_piece("Pawn", Player.WHITE, 4, 1)
game_state.add_piece("Pawn", Player.WHITE, 5, 1)
game_state.add_piece("Pawn", Player.WHITE, 6, 1)
game_state.add_piece("Pawn", Player.WHITE, 7, 1)

game_state.add_piece("Pawn", Player.BLACK, 0, 6)
game_state.add_piece("Pawn", Player.BLACK, 1, 6)
game_state.add_piece("Pawn", Player.BLACK, 2, 6)
game_state.add_piece("Pawn", Player.BLACK, 3, 6)
game_state.add_piece("Pawn", Player.BLACK, 4, 6)
game_state.add_piece("Pawn", Player.BLACK, 5, 6)
game_state.add_piece("Pawn", Player.BLACK, 6, 6)
game_state.add_piece("Pawn", Player.BLACK, 7, 6)

game_state.add_piece("Rook", Player.WHITE, 0, 0)
game_state.add_piece("Knight", Player.WHITE, 1, 0)
game_state.add_piece("Bishop", Player.WHITE, 2, 0)
game_state.add_piece("Queen", Player.WHITE, 3, 0)
game_state.add_piece("King", Player.WHITE, 4, 0)
game_state.add_piece("Bishop", Player.WHITE, 5, 0)
game_state.add_piece("Knight", Player.WHITE, 6, 0)
game_state.add_piece("Rook", Player.WHITE, 7, 0)

game_state.add_piece("Rook", Player.BLACK, 0, 7)
game_state.add_piece("Knight", Player.BLACK, 1, 7)
game_state.add_piece("Bishop", Player.BLACK, 2, 7)
game_state.add_piece("Queen", Player.BLACK, 3, 7)
game_state.add_piece("King", Player.BLACK, 4, 7)
game_state.add_piece("Bishop", Player.BLACK, 5, 7)
game_state.add_piece("Knight", Player.BLACK, 6, 7)
game_state.add_piece("Rook", Player.BLACK, 7, 7)

game_state.move_piece(0, 0, 2, 4)
if game_state.board[1][0] is not None:
    print(game_state.board[1][0].valid_moves())
# game_state.move_piece(4, 1, 4, 3)

print(game_state)

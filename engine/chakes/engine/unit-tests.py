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

import unittest as ut
from game_engine import *

# Patch piece.get_cooldown to always return 0.0 in order to not have to wait for cooldown unless self._enable_cooldown is True
piece_get_cooldown = Piece.get_cooldown
Piece.get_cooldown = lambda self: 0.0 if not getattr(self, '_enable_cooldown', False) else piece_get_cooldown(self) # type: ignore

class TestPieces(ut.TestCase):
    def test_rook(self):
        game_state = GameState.default()
        game_state.move_piece_str('A2', 'A4')
        game_state.move_piece_str('A1', 'A3')
        game_state.move_piece_str('A3', 'B3')
        self.assertEqual(
            poses_to_str(game_state.piece_at('B3').legal_moves()),
            {'A3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'B4', 'B5', 'B6', 'B7'},
        )

    def test_pawn(self):
        game_state = GameState.default()
        game_state.move_piece_str('B2', 'B4')
        game_state.move_piece_str('B4', 'B5')
        game_state.move_piece_str('B5', 'B6')
        self.assertEqual(
            poses_to_str(game_state.piece_at('B6').legal_moves()),
            {'A7', 'C7'},
        )

    def test_en_passent(self):
        game_state = GameState.default()
        game_state.move_piece_str('B2', 'B4')
        game_state.move_piece_str('B4', 'B5')
        game_state.move_piece_str('C7', 'C5')
        game_state.piece_at('C5')._enable_cooldown = True
        game_state.move_piece_str('B5', 'C6')
        self.assertIsNone(game_state.piece_at('C5'))

    def test_promotion(self):
        game_state = GameState.default()
        game_state.move_piece_str('A2', 'A4')
        game_state.move_piece_str('A4', 'A5')
        game_state.move_piece_str('A5', 'A6')
        game_state.move_piece_str('A6', 'B7')
        game_state.move_piece_str('B7', 'A8', info = 'Knight')
        self.assertEqual(
            game_state.piece_at('A8').name,
            'Knight',
        )

    def test_knight(self):
        game_state = GameState.default()
        game_state.move_piece_str('B1', 'C3')
        self.assertEqual(
            poses_to_str(game_state.piece_at('C3').legal_moves()),
            {'B1', 'A4', 'B5', 'D5', 'E4'},
        )

    def test_bishop(self):
        game_state = GameState.default()
        game_state.move_piece_str('D2', 'D3')
        game_state.move_piece_str('C1', 'E3')
        self.assertEqual(
            poses_to_str(game_state.piece_at('E3').legal_moves()),
            {'D2', 'C1', 'D4', 'C5', 'B6', 'A7', 'F4', 'G5', 'H6'},
        )

    def test_queen(self):
        game_state = GameState.default()
        game_state.move_piece_str('E2', 'E3')
        game_state.move_piece_str('D1', 'F3')
        self.assertEqual(
            poses_to_str(game_state.piece_at('F3').legal_moves()),
            {'E2', 'D1', 'E4', 'D5', 'C6', 'B7', 'F4', 'F5', 'F6', 'F7', 'G4', 'H5', 'H3', 'G3'},
        )

    def test_king(self):
        game_state = GameState.default()
        game_state.move_piece_str('E2', 'E4')
        game_state.move_piece_str('D7', 'D5')
        game_state.move_piece_str('D5', 'D4')
        game_state.move_piece_str('E1', 'E2')
        self.assertEqual(
            poses_to_str(game_state.piece_at('E2').legal_moves()),
            {'E1', 'D3', 'F3'},
        )

    def test_castling(self):
        game_state = GameState.default()
        game_state.move_piece_str('B1', 'A3')
        game_state.move_piece_str('B2', 'B3')
        game_state.move_piece_str('C1', 'B2')
        game_state.move_piece_str('E2', 'E3')
        game_state.move_piece_str('D1', 'F3')
        game_state.move_piece_str('F1', 'E2')
        game_state.move_piece_str('G1', 'H3')
        self.assertEqual(
            poses_to_str(game_state.piece_at('E1').legal_moves()),
            {'C1', 'D1', 'F1', 'G1'}

        )

        game_state.move_piece_str('E1', 'C1')
        self.assertEqual(
            game_state.piece_at('D1').name,
            'Rook',
        )

    def test_nightrider(self):
        game_state = GameState.default()
        game_state.add_piece_str('Nightrider', Player.WHITE, 'B1')
        self.assertEqual(
            poses_to_str(game_state.piece_at('B1').legal_moves()),
            {'A3', 'C3', 'D5', 'E7'}
        )

    def test_anti_king(self):
        game_state = GameState.default()
        game_state.add_piece_str('Anti-King', Player.WHITE, 'E6')
        game_state.move_piece_str('E2', 'E4')
        game_state.move_piece_str('E4', 'E5')
        game_state.move_piece_str('D7', 'D6')
        self.assertEqual(
            poses_to_str(game_state.piece_at('E6').legal_moves()),
            {'D7', 'E5', 'F6'}
        )

    def test_grasshopper(self):
        game_state = GameState.default()
        game_state.add_piece_str('Grasshopper', Player.WHITE, 'A5')
        game_state.move_piece_str('E7', 'E5')
        self.assertEqual(
            poses_to_str(game_state.piece_at('A5').legal_moves()),
            {'A8', 'D8', 'F5'},
        )


if __name__ == '__main__':
    ut.main()

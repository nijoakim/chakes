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
from chakes.engine.game_engine import GameState, Piece, Player, poses_to_str

# Patch piece.get_cooldown to always return 0.0 in order to not have to wait for cooldown unless self._enable_cooldown is True
piece_get_cooldown = Piece.get_cooldown
Piece.get_cooldown = lambda self: 0.0 if not getattr(self, '_enable_cooldown', False) else piece_get_cooldown(self) # type: ignore

class TestPieces(ut.TestCase):
    def test_rook(self):
        game_state = GameState.default()
        game_state.move_piece_str('A2', 'A4')
        game_state.move_piece_str('A1', 'A3')
        game_state.move_piece_str('A3', 'B3')

        piece: Piece | None = game_state.piece_at('B3')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'A3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'B4', 'B5', 'B6', 'B7'},
        )

    def test_pawn(self):
        game_state = GameState.default()
        game_state.move_piece_str('B2', 'B4')
        game_state.move_piece_str('B4', 'B5')
        game_state.move_piece_str('B5', 'B6')

        piece: Piece | None = game_state.piece_at('B6')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'A7', 'C7'},
        )

    def test_en_passent(self):
        game_state = GameState.default()
        game_state.move_piece_str('B2', 'B4')
        game_state.move_piece_str('B4', 'B5')
        game_state.move_piece_str('C7', 'C5')

        pawn: Piece | None = game_state.piece_at('C5')
        assert isinstance(pawn, Piece)
        game_state.piece_at('C5')._enable_cooldown = True # type: ignore
        
        game_state.move_piece_str('B5', 'C6')

        piece: Piece | None = game_state.piece_at('C5')

        self.assertIsNone(piece)

    def test_promotion(self):
        game_state = GameState.default()
        game_state.move_piece_str('A2', 'A4')
        game_state.move_piece_str('A4', 'A5')
        game_state.move_piece_str('A5', 'A6')
        game_state.move_piece_str('A6', 'B7')
        game_state.move_piece_str('B7', 'A8', info = 'Knight')

        piece: Piece | None = game_state.piece_at('A8')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            piece.name,
            'Knight',
        )

    def test_knight(self):
        game_state = GameState.default()
        game_state.move_piece_str('B1', 'C3')

        piece: Piece | None = game_state.piece_at('C3')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'B1', 'A4', 'B5', 'D5', 'E4'},
        )

    def test_bishop(self):
        game_state = GameState.default()
        game_state.move_piece_str('D2', 'D3')
        game_state.move_piece_str('C1', 'E3')

        piece: Piece | None = game_state.piece_at('E3')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'D2', 'C1', 'D4', 'C5', 'B6', 'A7', 'F4', 'G5', 'H6'},
        )

    def test_queen(self):
        game_state = GameState.default()
        game_state.move_piece_str('E2', 'E3')
        game_state.move_piece_str('D1', 'F3')

        piece: Piece | None = game_state.piece_at('F3')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'E2', 'D1', 'E4', 'D5', 'C6', 'B7', 'F4', 'F5', 'F6', 'F7', 'G4', 'H5', 'H3', 'G3'},
        )

    def test_king(self):
        game_state = GameState.default()
        game_state.move_piece_str('E2', 'E4')
        game_state.move_piece_str('D7', 'D5')
        game_state.move_piece_str('D5', 'D4')
        game_state.move_piece_str('E1', 'E2')

        piece: Piece | None = game_state.piece_at('E2')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
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

        king: Piece | None = game_state.piece_at('E1')
        assert isinstance(king, Piece)

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'C1', 'D1', 'F1', 'G1'}
        )

        game_state.move_piece_str('E1', 'C1')

        rook: Piece | None = game_state.piece_at('D1')
        assert isinstance(rook, Piece)

        self.assertEqual(rook.name, 'Rook')

    def test_check_mate(self):
        game_state = GameState.default()
        game_state.move_piece_str('F2', 'F3')
        game_state.move_piece_str('G2', 'G4')
        game_state.move_piece_str('E7', 'E6')

        self.assertIsNone(game_state.winner())

        game_state.move_piece_str('D8', 'H4')

        self.assertEqual(
            game_state.winner(),
            Player.BLACK,
        )

    def test_nightrider(self):
        game_state = GameState.default()
        game_state.add_piece_str('Nightrider', Player.WHITE, 'B1')

        piece: Piece | None = game_state.piece_at('B1')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'A3', 'C3', 'D5', 'E7'}
        )

    def test_anti_king(self):
        game_state = GameState.default()
        game_state.add_piece_str('Anti-King', Player.WHITE, 'E6')
        game_state.move_piece_str('E2', 'E4')
        game_state.move_piece_str('E4', 'E5')
        game_state.move_piece_str('D7', 'D6')

        piece: Piece | None = game_state.piece_at('E6')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'D7', 'E5', 'F6'}
        )

    def test_grasshopper(self):
        game_state = GameState.default()
        game_state.add_piece_str('Grasshopper', Player.WHITE, 'A5')
        game_state.move_piece_str('E7', 'E5')

        piece: Piece | None = game_state.piece_at('A5')
        self.assertIsInstance(piece, Piece)

        self.assertEqual(
            poses_to_str(piece.legal_moves()),
            {'A8', 'D8', 'F5'},
        )


if __name__ == '__main__':
    ut.main()

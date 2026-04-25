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
from typing import Optional
from engine.chakes.engine.game_engine import *

# Patch piece.get_cooldown to always return 0.0 in order to not have to wait for cooldown unless self._enable_cooldown is True
piece_get_cooldown = Piece.get_cooldown
Piece.get_cooldown = lambda self: 0.0 if not getattr(self, '_enable_cooldown', False) else piece_get_cooldown(self) # type: ignore

class TestPieces(ut.TestCase):
    def test_rook(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('A2', 'A4')
        game_state.move_piece_str('A1', 'A3')
        game_state.move_piece_str('A3', 'B3')

        rook: Optional[Piece] = game_state.piece_at('B3')
        assert rook is not None

        self.assertEqual(
            poses_to_str(rook.legal_moves()),
            {'A3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'B4', 'B5', 'B6', 'B7'},
        )

    def test_pawn(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('B2', 'B4')
        game_state.move_piece_str('B4', 'B5')
        game_state.move_piece_str('B5', 'B6')

        pawn: Optional[Piece] = game_state.piece_at('B6')
        assert pawn is not None

        self.assertEqual(
            poses_to_str(pawn.legal_moves()),
            {'A7', 'C7'},
        )

    def test_en_passent(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('B2', 'B4')
        game_state.move_piece_str('B4', 'B5')
        game_state.move_piece_str('C7', 'C5')

        enemy_pawn: Optional[Piece] = game_state.piece_at('C5')
        assert enemy_pawn is not None

        enemy_pawn._enable_cooldown = True # type: ignore
        game_state.move_piece_str('B5', 'C6')

        captured_pawn: Optional[Piece] = game_state.piece_at('C5')
        self.assertIsNone(captured_pawn)

    def test_promotion(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('A2', 'A4')
        game_state.move_piece_str('A4', 'A5')
        game_state.move_piece_str('A5', 'A6')
        game_state.move_piece_str('A6', 'B7')
        game_state.move_piece_str('B7', 'A8', info = 'Knight')

        knight: Optional[Piece] = game_state.piece_at('A8')
        assert knight is not None

        self.assertEqual(
            knight.name,
            'Knight',
        )

    def test_knight(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('B1', 'C3')

        knight: Optional[Piece] = game_state.piece_at('C3')
        assert knight is not None

        self.assertEqual(
            poses_to_str(knight.legal_moves()),
            {'B1', 'A4', 'B5', 'D5', 'E4'},
        )

    def test_bishop(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('D2', 'D3')
        game_state.move_piece_str('C1', 'E3')

        bishop: Optional[Piece] = game_state.piece_at('E3')
        assert bishop is not None

        self.assertEqual(
            poses_to_str(bishop.legal_moves()),
            {'D2', 'C1', 'D4', 'C5', 'B6', 'A7', 'F4', 'G5', 'H6'},
        )

    def test_queen(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('E2', 'E3')
        game_state.move_piece_str('D1', 'F3')

        queen: Optional[Piece] = game_state.piece_at('F3')
        assert queen is not None

        self.assertEqual(
            poses_to_str(queen.legal_moves()),
            {'E2', 'D1', 'E4', 'D5', 'C6', 'B7', 'F4', 'F5', 'F6', 'F7', 'G4', 'H5', 'H3', 'G3'},
        )

    def test_king(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('E2', 'E3')
        game_state.move_piece_str('D7', 'D5')
        game_state.move_piece_str('D5', 'D4')
        game_state.move_piece_str('F7', 'F5')
        game_state.move_piece_str('F5', 'F4')
        game_state.move_piece_str('D8', 'D7')
        game_state.move_piece_str('D7', 'E6')
        game_state.move_piece_str('E1', 'E2')

        pawn: Optional[Piece] = game_state.piece_at('E3')
        assert pawn is not None

        self.assertEqual(
            poses_to_str(pawn.legal_moves()),
            {'E4'},
        )

        game_state.move_piece_str('F4', 'E3')

        king: Optional[Piece] = game_state.piece_at('E2')
        assert king is not None

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'E1', 'D3', 'F3'},
        )

    def test_castling(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('B1', 'A3')
        game_state.move_piece_str('B2', 'B3')
        game_state.move_piece_str('C1', 'B2')
        game_state.move_piece_str('E2', 'E3')
        game_state.move_piece_str('D1', 'F3')
        game_state.move_piece_str('F1', 'E2')

        king: Optional[Piece] = game_state.piece_at('E1')
        assert isinstance(king, Piece)

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'C1', 'D1', 'F1'}
        )

        game_state.move_piece_str('G1', 'H3')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'C1', 'D1', 'F1', 'G1'}
        )

        game_state.move_piece_str('E1', 'C1')

        rook: Optional[Piece] = game_state.piece_at('D1')
        assert isinstance(rook, Piece)

        self.assertEqual(rook.name, 'Rook')

    def test_check_mate(self) -> None:
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

    def test_nightrider(self) -> None:
        game_state = GameState.default()
        game_state.add_piece_str('Nightrider', Player.WHITE, 'B1')

        nightrider: Optional[Piece] = game_state.piece_at('B1')
        assert nightrider is not None

        self.assertEqual(
            poses_to_str(nightrider.legal_moves()),
            {'A3', 'C3', 'D5', 'E7'}
        )

    def test_anti_king(self) -> None:
        game_state = GameState.default()
        game_state.add_piece_str('Anti-King', Player.WHITE, 'E6')
        game_state.move_piece_str('E2', 'E4')
        game_state.move_piece_str('E4', 'E5')
        game_state.move_piece_str('D7', 'D6')

        anti_king: Optional[Piece] = game_state.piece_at('E6')
        assert anti_king is not None

        self.assertEqual(
            poses_to_str(anti_king.legal_moves()),
            {'D7', 'E5', 'F5', 'F6'}
        )

    def test_grasshopper(self) -> None:
        game_state = GameState.default()
        game_state.add_piece_str('Grasshopper', Player.WHITE, 'A5')
        game_state.move_piece_str('E7', 'E5')

        grasshopper: Optional[Piece] = game_state.piece_at('A5')
        assert grasshopper is not None

        self.assertEqual(
            poses_to_str(grasshopper.legal_moves()),
            {'A8', 'D8', 'F5'},
        )


if __name__ == '__main__':
    ut.main()

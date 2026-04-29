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
        game_state.move_piece_str('a2', 'a4')
        game_state.move_piece_str('a1', 'a3')
        game_state.move_piece_str('a3', 'b3')

        rook: Optional[Piece] = game_state.piece_at('b3')
        assert rook is not None

        self.assertEqual(
            poses_to_str(rook.legal_moves()),
            {'a3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3', 'b4', 'b5', 'b6', 'b7'},
        )

    def test_pawn(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('b2', 'b4')
        game_state.move_piece_str('b4', 'b5')
        game_state.move_piece_str('b5', 'b6')

        pawn: Optional[Piece] = game_state.piece_at('b6')
        assert pawn is not None

        self.assertEqual(
            poses_to_str(pawn.legal_moves()),
            {'a7', 'c7'},
        )

    def test_en_passant(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('b2', 'b4')
        game_state.move_piece_str('b4', 'b5')
        game_state.move_piece_str('c7', 'c5')

        enemy_pawn: Optional[Piece] = game_state.piece_at('c5')
        assert enemy_pawn is not None

        enemy_pawn._enable_cooldown = True # type: ignore
        game_state.move_piece_str('b5', 'c6')

        captured_pawn: Optional[Piece] = game_state.piece_at('c5')
        self.assertIsNone(captured_pawn)

    def test_promotion(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('a2', 'a4')
        game_state.move_piece_str('a4', 'a5')
        game_state.move_piece_str('a5', 'a6')
        game_state.move_piece_str('a6', 'b7')
        game_state.move_piece_str('b7', 'a8', info = 'Knight')

        knight: Optional[Piece] = game_state.piece_at('a8')
        assert knight is not None

        self.assertEqual(
            knight.name,
            'Knight',
        )

    def test_knight(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('b1', 'c3')

        knight: Optional[Piece] = game_state.piece_at('c3')
        assert knight is not None

        self.assertEqual(
            poses_to_str(knight.legal_moves()),
            {'b1', 'a4', 'b5', 'd5', 'e4'},
        )

    def test_bishop(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('d2', 'd3')
        game_state.move_piece_str('c1', 'e3')

        bishop: Optional[Piece] = game_state.piece_at('e3')
        assert bishop is not None

        self.assertEqual(
            poses_to_str(bishop.legal_moves()),
            {'d2', 'c1', 'd4', 'c5', 'b6', 'a7', 'f4', 'g5', 'h6'},
        )

    def test_queen(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('e2', 'e3')
        game_state.move_piece_str('d1', 'f3')

        queen: Optional[Piece] = game_state.piece_at('f3')
        assert queen is not None

        self.assertEqual(
            poses_to_str(queen.legal_moves()),
            {'e2', 'd1', 'e4', 'd5', 'c6', 'b7', 'f4', 'f5', 'f6', 'f7', 'g4', 'h5', 'h3', 'g3'},
        )

    def test_king(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('e2', 'e3')
        game_state.move_piece_str('d7', 'd5')
        game_state.move_piece_str('d5', 'd4')
        game_state.move_piece_str('f7', 'f5')
        game_state.move_piece_str('f5', 'f4')
        game_state.move_piece_str('d8', 'd7')
        game_state.move_piece_str('d7', 'e6')
        game_state.move_piece_str('e1', 'e2')

        pawn: Optional[Piece] = game_state.piece_at('e3')
        assert pawn is not None

        self.assertEqual(
            poses_to_str(pawn.legal_moves()),
            {'e4'},
        )

        game_state.move_piece_str('f4', 'e3')

        king: Optional[Piece] = game_state.piece_at('e2')
        assert king is not None

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'e1', 'd3', 'f3'},
        )

    def test_castling(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('b1', 'a3')
        game_state.move_piece_str('b2', 'b3')
        game_state.move_piece_str('c1', 'b2')
        game_state.move_piece_str('e2', 'e3')
        game_state.move_piece_str('d1', 'f3')
        game_state.move_piece_str('f1', 'e2')

        king: Optional[Piece] = game_state.piece_at('e1')
        assert isinstance(king, Piece)

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'c1', 'd1', 'f1'},
        )

        game_state.move_piece_str('g1', 'h3')

        # Attack E1
        game_state.move_piece_str('b8', 'c6')
        game_state.move_piece_str('c6', 'b4')
        game_state.move_piece_str('b4', 'd3')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'d1', 'f1'},
        )

        # Attack D1
        game_state.move_piece_str('d3', 'c5')
        game_state.move_piece_str('c5', 'a4')
        game_state.move_piece_str('a4', 'c3')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'f1', 'g1'},
        )

        # Attack C1
        game_state.move_piece_str('c3', 'a4')
        game_state.move_piece_str('a4', 'c5')
        game_state.move_piece_str('c5', 'b3')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'d1', 'f1', 'g1'},
        )

        # Attack F1
        game_state.move_piece_str('b3', 'c5')
        game_state.move_piece_str('c5', 'e4')
        game_state.move_piece_str('e4', 'g3')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'c1', 'd1'},
        )

        # Attack G1
        game_state.move_piece_str('g3', 'h5')
        game_state.move_piece_str('h5', 'f4')
        game_state.move_piece_str('f4', 'h3')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'c1', 'd1', 'f1'},
        )

        # Stop attack
        game_state.move_piece_str('h3', 'g5')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'c1', 'd1', 'f1', 'g1'},
        )

        # Attack with pawn
        game_state.move_piece_str('d7', 'd5')
        game_state.move_piece_str('d5', 'd4')
        game_state.move_piece_str('d4', 'd3')
        game_state.move_piece_str('d3', 'e2')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'e2'},
        )

        # Stop attack
        game_state.move_piece_str('f3', 'e2')

        # Attack with pawn
        game_state.move_piece_str('c7', 'c5')
        game_state.move_piece_str('c5', 'c4')
        game_state.move_piece_str('c4', 'c3')
        game_state.move_piece_str('c3', 'd2')

        self.assertEqual(
            poses_to_str(king.legal_moves()),
            {'d1', 'f1'},
        )

        # Stop attack
        game_state.move_piece_str('e2', 'd2')

        # Castle
        game_state.move_piece_str('e1', 'c1')

        rook: Optional[Piece] = game_state.piece_at('d1')
        assert isinstance(rook, Piece)

        self.assertEqual(rook.name, 'Rook')

    def test_checkmate(self) -> None:
        game_state = GameState.default()
        game_state.move_piece_str('e7', 'e6')
        game_state.move_piece_str('d8', 'e7')
        game_state.move_piece_str('e7', 'b4')
        game_state.move_piece_str('b4', 'd2')

        self.assertIsNone(game_state.winner())

        game_state.move_piece_str('d2', 'a5')

        self.assertIsNone(game_state.winner())

        queen: Optional[Piece] = game_state.piece_at('a5')
        assert queen is not None

        # Assert King can not be captured
        self.assertTrue('e1' not in poses_to_str(queen.legal_moves()))

        game_state.move_piece_str('b1', 'd2')
        game_state.move_piece_str('h2', 'h3')
        game_state.move_piece_str('a5', 'f5')
        game_state.move_piece_str('f5', 'f2')

        self.assertIsNone(game_state.winner())

        game_state.move_piece_str('f2', 'g3')

        self.assertEqual(
            game_state.winner(),
            Player.BLACK,
        )

    def test_nightrider(self) -> None:
        game_state = GameState.default()
        game_state.add_piece_str('Nightrider', Player.WHITE, 'b1')

        nightrider: Optional[Piece] = game_state.piece_at('b1')
        assert nightrider is not None

        self.assertEqual(
            poses_to_str(nightrider.legal_moves()),
            {'a3', 'c3', 'd5', 'e7'}
        )

    def test_anti_king(self) -> None:
        game_state = GameState.anti_king_chess()

        game_state.move_piece_str('d3', 'c3')
        game_state.move_piece_str('d2', 'd4')
        game_state.move_piece_str('d4', 'd5')
        game_state.move_piece_str('e7', 'e6')

        anti_king: Optional[Piece] = game_state.piece_at('d6')
        assert anti_king is not None

        self.assertEqual(
            poses_to_str(anti_king.legal_moves()),
            {'c6', 'c5', 'd5', 'e7'}
        )

    def test_anti_checkmate(self) -> None:
        game_state = GameState.anti_king_chess()

        anti_king: Optional[Piece] = game_state.piece_at('d6')
        assert anti_king is not None

        # Move pawns
        game_state.move_piece_str('a7', 'a5')
        game_state.move_piece_str('b7', 'b5')

        # Set-up knight for blocking
        game_state.move_piece_str('b8', 'a6')
        game_state.move_piece_str('a6', 'c5')

        # Move anti-king to edge
        game_state.move_piece_str('d6', 'c6')
        game_state.move_piece_str('c6', 'b6')
        game_state.move_piece_str('b6', 'a6')

        # Move pawns
        game_state.move_piece_str('c7', 'c6')
        game_state.move_piece_str('e7', 'e6')

        # Move queen
        game_state.move_piece_str('d8', 'e7')

        # Block bishop with knight
        game_state.move_piece_str('c5', 'b7')

        self.assertIsNone(game_state.winner())

        # Move rook
        game_state.move_piece_str('a8', 'b8')

        self.assertEqual(
            game_state.winner(),
            Player.BLACK,
        )

    def test_grasshopper(self) -> None:
        game_state = GameState.default()
        game_state.add_piece_str('Grasshopper', Player.WHITE, 'a5')
        game_state.move_piece_str('e7', 'e5')

        grasshopper: Optional[Piece] = game_state.piece_at('a5')
        assert grasshopper is not None

        self.assertEqual(
            poses_to_str(grasshopper.legal_moves()),
            {'a8', 'd8', 'f5'},
        )

    def test_camel(self) -> None:
        game_state = GameState.default()
        game_state.remove_piece_str('b1')
        game_state.add_piece_str('Camel', Player.WHITE, 'b1')
        game_state.move_piece_str('b1', 'c4')

        camel: Optional[Piece] = game_state.piece_at('c4')
        assert camel is not None

        self.assertEqual(
            poses_to_str(camel.legal_moves()),
            {'b1', 'b7', 'd7', 'f3', 'f5'},
        )

    def test_berolina_pawn(self) -> None:
        game_state = GameState.berolina_chess()
        game_state.move_piece_str('a2', 'c4')
        game_state.move_piece_str('c4', 'b5')
        game_state.move_piece_str('b5', 'c6')

        berolina_pawn: Optional[Piece] = game_state.piece_at('c6')
        assert berolina_pawn is not None

        self.assertEqual(
            poses_to_str(berolina_pawn.legal_moves()),
            {'c7'},
        )

        game_state.move_piece_str('c6', 'c7')
        game_state.move_piece_str('c7', 'c8', info = 'Knight')

        knight: Optional[Piece] = game_state.piece_at('c8')
        assert knight is not None

        self.assertEqual(
            knight.name,
            'Knight',
        )

    def test_chameleon(self) -> None:
        game_state = GameState.default()
        game_state.remove_piece_str('b1')
        game_state.add_piece_str('Chameleon', Player.WHITE, 'b1')

        chameleon: Optional[Piece] = game_state.piece_at('b1')
        assert chameleon is not None

        # Is knight
        self.assertEqual(
            poses_to_str(chameleon.legal_moves()),
            {'a3', 'c3'},
        )

        # Shift into bishop
        game_state.move_piece_str('b1', 'c3')
        self.assertEqual(
            poses_to_str(chameleon.legal_moves()),
            {'b4', 'a5', 'd4', 'e5', 'f6', 'g7'},
        )

        # Shift into rook
        game_state.move_piece_str('c3', 'e5')
        self.assertEqual(
            poses_to_str(chameleon.legal_moves()),
            {'a5', 'b5', 'c5', 'd5', 'f5', 'g5', 'h5', 'e3', 'e4', 'e6', 'e7'},
        )

        # Shift into queen
        game_state.move_piece_str('e5', 'c5')
        self.assertEqual(
            poses_to_str(chameleon.legal_moves()),
            {'a5', 'b5', 'd5', 'e5', 'f5', 'g5', 'h5', 'c3', 'c4', 'c6', 'c7', 'a7', 'b6', 'd4', 'e3', 'a3', 'b4', 'd6', 'e7'},
        )

        # Shift back into knight
        game_state.move_piece_str('c5', 'e3')
        self.assertEqual(
            poses_to_str(chameleon.legal_moves()),
            {'c4', 'd5', 'f5', 'g4'},
        )


if __name__ == '__main__':
    ut.main()

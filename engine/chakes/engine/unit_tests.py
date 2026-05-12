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
from engine.chakes.engine.engine import Board, Piece, Player, Pos

# Patch piece.get_cooldown to always return 0.0 in order to not have to wait for cooldown unless self._enable_cooldown is True
piece_get_cooldown = Piece.get_cooldown
Piece.get_cooldown = lambda self: 0.0 if not getattr(self, '_enable_cooldown', False) else piece_get_cooldown(self) # type: ignore

class TestPieces(ut.TestCase):
    def test_rook(self) -> None:
        board = Board.orthodox()

        board.move_piece(Pos('a2'), Pos('a4'))
        board.move_piece(Pos('a1'), Pos('a3'))
        board.move_piece(Pos('a3'), Pos('b3'))

        rook: Piece | None = board.piece_at(Pos('b3'))
        assert rook is not None

        self.assertEqual(
            rook.legal_moves(),
            set(map(Pos, {'a3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3', 'b4', 'b5', 'b6', 'b7'})),
        )

    def test_pawn(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('b2'), Pos('b4'))
        board.move_piece(Pos('b4'), Pos('b5'))
        board.move_piece(Pos('b5'), Pos('b6'))

        pawn: Piece | None = board.piece_at(Pos('b6'))
        assert pawn is not None

        self.assertEqual(
            pawn.legal_moves(),
            set(map(Pos, {'a7', 'c7'})),
        )

    def test_en_passant(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('b2'), Pos('b4'))
        board.move_piece(Pos('b4'), Pos('b5'))
        board.move_piece(Pos('c7'), Pos('c5'))

        enemy_pawn: Piece | None = board.piece_at(Pos('c5'))
        assert enemy_pawn is not None

        enemy_pawn._enable_cooldown = True # type: ignore
        board.move_piece(Pos('b5'), Pos('c6'))

        captured_pawn: Piece | None = board.piece_at(Pos('c5'))
        self.assertIsNone(captured_pawn)

    def test_promotion(self) -> None:
        board = Board.orthodox()

        pawn: Piece | None = board.piece_at(Pos('a2'))
        assert pawn is not None

        pawn.move(Pos('a4'))
        pawn.move(Pos('a5'))
        pawn.move(Pos('a6'))
        pawn.move(Pos('b7'))
        pawn.move(Pos('a8'), info = 'Knight')

        knight: Piece | None = board.piece_at(Pos('a8'))
        assert knight is not None

        self.assertEqual(
            knight.name,
            'Knight',
        )

    def test_knight(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('b1'), Pos('c3'))

        knight: Piece | None = board.piece_at(Pos('c3'))
        assert knight is not None

        self.assertEqual(
            knight.legal_moves(),
            set(map(Pos, {'b1', 'a4', 'b5', 'd5', 'e4'})),
        )

    def test_bishop(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('d2'), Pos('d3'))
        board.move_piece(Pos('c1'), Pos('e3'))

        bishop: Piece | None = board.piece_at(Pos('e3'))
        assert bishop is not None

        self.assertEqual(
            bishop.legal_moves(),
            set(map(Pos, {'d2', 'c1', 'd4', 'c5', 'b6', 'a7', 'f4', 'g5', 'h6'})),
        )

    def test_queen(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('e2'), Pos('e3'))
        board.move_piece(Pos('d1'), Pos('f3'))

        queen: Piece | None = board.piece_at(Pos('f3'))
        assert queen is not None

        self.assertEqual(
            queen.legal_moves(),
            set(map(Pos, {'e2', 'd1', 'e4', 'd5', 'c6', 'b7', 'f4', 'f5', 'f6', 'f7', 'g4', 'h5', 'h3', 'g3'})),
        )

    def test_king(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('e2'), Pos('e3'))
        board.move_piece(Pos('d7'), Pos('d5'))
        board.move_piece(Pos('d5'), Pos('d4'))
        board.move_piece(Pos('f7'), Pos('f5'))
        board.move_piece(Pos('f5'), Pos('f4'))
        board.move_piece(Pos('d8'), Pos('d7'))
        board.move_piece(Pos('d7'), Pos('e6'))
        board.move_piece(Pos('e1'), Pos('e2'))

        pawn: Piece | None = board.piece_at(Pos('e3'))
        assert pawn is not None

        self.assertEqual(
            pawn.legal_moves(),
            set(map(Pos, {'e4'})),
        )

        board.move_piece(Pos('f4'), Pos('e3'))

        king: Piece | None = board.piece_at(Pos('e2'))
        assert king is not None

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'e1', 'd3', 'f3'})),
        )

    def test_castling(self) -> None:
        board = Board.orthodox()

        queen: Piece | None = board.piece_at(Pos('d1'))
        assert queen is not None

        board.move_piece(Pos('b1'), Pos('a3'))
        board.move_piece(Pos('b2'), Pos('b3'))
        board.move_piece(Pos('c1'), Pos('b2'))
        board.move_piece(Pos('e2'), Pos('e3'))
        queen.move(Pos('f3'))
        board.move_piece(Pos('f1'), Pos('e2'))

        king: Piece | None = board.piece_at(Pos('e1'))
        assert king is not None

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'c1', 'd1', 'f1'})),
        )

        board.move_piece(Pos('g1'), Pos('h3'))

        knight: Piece | None = board.piece_at(Pos('b8'))
        assert knight is not None

        # Attack e1
        knight.move(Pos('c6'))
        knight.move(Pos('b4'))
        knight.move(Pos('d3'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'d1', 'f1'})),
        )

        # Attack d1
        knight.move(Pos('c5'))
        knight.move(Pos('a4'))
        knight.move(Pos('c3'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'f1', 'g1'})),
        )

        # Attack c1
        knight.move(Pos('a4'))
        knight.move(Pos('c5'))
        knight.move(Pos('b3'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'d1', 'f1', 'g1'})),
        )

        # Attack f1
        knight.move(Pos('c5'))
        knight.move(Pos('e4'))
        knight.move(Pos('g3'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'c1', 'd1'})),
        )

        # Attack g1
        knight.move(Pos('h5'))
        knight.move(Pos('f4'))
        knight.move(Pos('h3'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'c1', 'd1', 'f1'})),
        )

        # Stop attack
        knight.move(Pos('g5'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'c1', 'd1', 'f1', 'g1'})),
        )

        pawn: Piece | None = board.piece_at(Pos('d7'))
        assert pawn is not None

        # Attack with pawn
        pawn.move(Pos('d5'))
        pawn.move(Pos('d4'))
        pawn.move(Pos('d3'))
        pawn.move(Pos('e2'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'e2'})),
        )

        # Stop pawn
        queen.move(Pos('e2'))

        # Attack with pawn
        board.move_piece(Pos('c7'), Pos('c5'))
        board.move_piece(Pos('c5'), Pos('c4'))
        board.move_piece(Pos('c4'), Pos('c3'))
        board.move_piece(Pos('c3'), Pos('d2'))

        self.assertEqual(
            king.legal_moves(),
            set(map(Pos, {'d1', 'f1'})),
        )

        # Stop attack
        queen.move(Pos('d2'))

        # Castle
        king.move(Pos('c1'))

        rook: Piece | None = board.piece_at(Pos('d1'))
        assert rook is not None

        self.assertEqual(rook.name, 'Rook')

    def test_checkmate(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('e7'), Pos('e6'))
        board.move_piece(Pos('d8'), Pos('e7'))
        board.move_piece(Pos('e7'), Pos('b4'))
        board.move_piece(Pos('b4'), Pos('d2'))

        queen: Piece | None = board.piece_at(Pos('d2'))
        assert queen is not None

        self.assertIsNone(board.winner())

        queen.move(Pos('a5'))

        self.assertIsNone(board.winner())

        # Assert King can not be captured
        self.assertTrue('e1' not in queen.legal_moves())

        board.move_piece(Pos('b1'), Pos('d2'))
        board.move_piece(Pos('h2'), Pos('h3'))

        queen.move(Pos('f5'))
        queen.move(Pos('f2'))

        self.assertIsNone(board.winner())

        queen.move(Pos('g3'))

        self.assertEqual(board.winner(), Player.BLACK)

    def test_draw(self) -> None:
        board = Board.orthodox()
        board.move_piece(Pos('e7'), Pos('e6'))

        queen: Piece | None = board.piece_at(Pos('d8'))
        assert queen is not None

        # Capture all pieces
        queen.move(Pos('h4'))
        queen.move(Pos('h2'))
        queen.move(Pos('h1'))
        queen.move(Pos('g1'))
        queen.move(Pos('g2'))
        queen.move(Pos('f2'))
        queen.move(Pos('f1'))
        queen.move(Pos('e2'))
        queen.move(Pos('d2'))
        queen.move(Pos('d1'))
        queen.move(Pos('c1'))
        queen.move(Pos('c2'))
        queen.move(Pos('b2'))
        queen.move(Pos('b1'))
        queen.move(Pos('a1'))
        queen.move(Pos('a2'))

        king: Piece | None = board.piece_at(Pos('e1'))
        assert king is not None

        # Move King to corner
        king.move(Pos('f1'))
        king.move(Pos('g1'))
        king.move(Pos('h1'))

        # Stalemate
        queen.move(Pos('f2'))

        self.assertEqual(
            board.winner(),
            Player.NEUTRAL,
        )

    def test_nightrider(self) -> None:
        board = Board.orthodox()
        board.remove_piece_at(Pos('b1'))
        board.add_new_piece('Nightrider', Player.WHITE, Pos('b1'))

        nightrider: Piece | None = board.piece_at(Pos('b1'))
        assert nightrider is not None

        self.assertEqual(
            nightrider.legal_moves(),
            set(map(Pos, {'a3', 'c3', 'd5', 'e7'})),
        )

    def test_anti_king(self) -> None:
        board = Board.anti_king_chess()

        board.move_piece(Pos('d3'), Pos('c3'))
        board.move_piece(Pos('d2'), Pos('d4'))
        board.move_piece(Pos('d4'), Pos('d5'))
        board.move_piece(Pos('e7'), Pos('e6'))

        anti_king: Piece | None = board.piece_at(Pos('d6'))
        assert anti_king is not None

        self.assertEqual(
            anti_king.legal_moves(),
            set(map(Pos, {'c6', 'c5', 'd5', 'e7'})),
        )

    def test_anti_checkmate(self) -> None:
        board = Board.anti_king_chess()

        anti_king: Piece | None = board.piece_at(Pos('d6'))
        assert anti_king is not None

        # Move pawns
        board.move_piece(Pos('a7'), Pos('a5'))
        board.move_piece(Pos('b7'), Pos('b5'))

        # Set-up knight for blocking
        board.move_piece(Pos('b8'), Pos('a6'))
        board.move_piece(Pos('a6'), Pos('c5'))

        # Move anti-king to edge
        anti_king.move(Pos('c6'))
        anti_king.move(Pos('b6'))
        anti_king.move(Pos('a6'))

        # Move pawns
        board.move_piece(Pos('c7'), Pos('c6'))
        board.move_piece(Pos('e7'), Pos('e6'))

        # Move queen
        board.move_piece(Pos('d8'), Pos('e7'))

        # Block bishop with knight
        board.move_piece(Pos('c5'), Pos('b7'))

        self.assertIsNone(board.winner())

        # Move rook
        board.move_piece(Pos('a8'), Pos('b8'))

        self.assertEqual(board.winner(), Player.BLACK)

    def test_grasshopper(self) -> None:
        board = Board.orthodox()
        board.add_new_piece('Grasshopper', Player.WHITE, Pos('a5'))
        board.move_piece(Pos('e7'), Pos('e5'))

        grasshopper: Piece | None = board.piece_at(Pos('a5'))
        assert grasshopper is not None

        self.assertEqual(
            grasshopper.legal_moves(),
            set(map(Pos, {'a8', 'd8', 'f5'})),
        )

    def test_camel(self) -> None:
        board = Board.orthodox()
        board.remove_piece_at(Pos('b1'))
        board.add_new_piece('Camel', Player.WHITE, Pos('b1'))
        board.move_piece(Pos('b1'), Pos('c4'))

        camel: Piece | None = board.piece_at(Pos('c4'))
        assert camel is not None

        self.assertEqual(
            camel.legal_moves(),
            set(map(Pos, {'b1', 'b7', 'd7', 'f3', 'f5'})),
        )

    def test_berolina_pawn(self) -> None:
        board = Board.berolina_chess()

        berolina_pawn: Piece | None = board.piece_at(Pos('a2'))
        assert berolina_pawn is not None

        berolina_pawn.move(Pos('c4'))
        berolina_pawn.move(Pos('b5'))
        berolina_pawn.move(Pos('c6'))

        self.assertEqual(
            berolina_pawn.legal_moves(),
            set(map(Pos, {'c7'})),
        )

        berolina_pawn.move(Pos('c7'))
        berolina_pawn.move(Pos('c8'), info = 'Knight')

        knight: Piece | None = board.piece_at(Pos('c8'))
        assert knight is not None

        self.assertEqual(
            knight.name,
            'Knight',
        )

    def test_chameleon(self) -> None:
        board = Board.orthodox()
        board.remove_piece_at(Pos('b1'))
        board.add_new_piece('Chameleon', Player.WHITE, Pos('b1'))

        chameleon: Piece | None = board.piece_at(Pos('b1'))
        assert chameleon is not None

        # Is knight
        self.assertEqual(
            chameleon.legal_moves(),
            set(map(Pos, {'a3', 'c3'})),
        )

        # Shift into bishop
        chameleon.move(Pos('c3'))
        self.assertEqual(
            chameleon.legal_moves(),
            set(map(Pos, {'b4', 'a5', 'd4', 'e5', 'f6', 'g7'})),
        )

        # Shift into rook
        chameleon.move(Pos('e5'))
        self.assertEqual(
            chameleon.legal_moves(),
            set(map(Pos, {'a5', 'b5', 'c5', 'd5', 'f5', 'g5', 'h5', 'e3', 'e4', 'e6', 'e7'})),
        )

        # Shift into queen
        chameleon.move(Pos('c5'))
        self.assertEqual(
            chameleon.legal_moves(),
            set(map(Pos, {'a5', 'b5', 'd5', 'e5', 'f5', 'g5', 'h5', 'c3', 'c4', 'c6', 'c7', 'a7', 'b6', 'd4', 'e3', 'a3', 'b4', 'd6', 'e7'})),
        )

        # Shift back into knight
        chameleon.move(Pos('e3'))
        self.assertEqual(
            chameleon.legal_moves(),
            set(map(Pos, {'c4', 'd5', 'f5', 'g4'})),
        )

    def test_gryphon(self) -> None:
        board = Board.orthodox()
        board.remove_piece_at(Pos('a1'))
        board.add_new_piece('Gryphon', Player.WHITE, Pos('a1'))
        board.move_piece(Pos('b2'), Pos('b4'))
        board.move_piece(Pos('a1'), Pos('b3'))

        gryphon: Piece | None = board.piece_at(Pos('b3'))
        assert gryphon is not None

        self.assertEqual(
            gryphon.legal_moves(),
            set(map(Pos, {'a3', 'a4', 'a5', 'a6', 'a7', 'c3', 'c4', 'c5', 'c6', 'c7', 'd4', 'e4', 'f4', 'g4', 'h4'})),
        )

    def test_knighted_chess(self) -> None:
        board = Board.knighted_chess()

        archbishop: Piece | None = board.piece_at(Pos('c1'))
        assert archbishop is not None

        archbishop.move(Pos('d3'))

        self.assertEqual(
            archbishop.legal_moves(),
            set(map(Pos, {'c4', 'b5', 'a6', 'e4', 'f5', 'g6', 'h7', 'b4', 'c5', 'e5', 'f4', 'c1'})),
        )

        chancellor: Piece | None = board.piece_at(Pos('h1'))
        assert chancellor is not None

        chancellor.move(Pos('g3'))

        self.assertEqual(
            chancellor.legal_moves(),
            set(map(Pos, {'e3', 'f3', 'h3', 'i3', 'j3', 'g4', 'g5', 'g6', 'g7', 'e4', 'f5', 'h5', 'i4', 'h1'})),
        )

    def test_ghost_rook(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('a1'))
        board.add_new_piece('Ghost Rook', Player.WHITE, Pos('a1'))

        ghost_rook: Piece | None = board.piece_at(Pos('a1'))
        assert ghost_rook is not None

        self.assertEqual(
            ghost_rook.legal_moves(),
            set(map(Pos, {'a3', 'a4', 'a5', 'a6', 'a7', 'a8'}))
        )

    def test_ghost_bishop(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('c1'))
        board.add_new_piece('Ghost Bishop', Player.WHITE, Pos('c1'))

        ghost_bishop: Piece | None = board.piece_at(Pos('c1'))
        assert ghost_bishop is not None

        ghost_bishop.move(Pos('a3'))

        self.assertEqual(
            ghost_bishop.legal_moves(),
            set(map(Pos, {'c1', 'b4', 'c5', 'd6', 'e7', 'f8'})),
        )

    def test_ghost_queen(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('d1'))
        board.add_new_piece('Ghost Queen', Player.WHITE, Pos('d1'))

        ghost_queen: Piece | None = board.piece_at(Pos('d1'))
        assert ghost_queen is not None

        self.assertEqual(
            ghost_queen.legal_moves(),
            set(map(Pos, {'b3', 'a4', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'f3', 'g4', 'h5'})),
        )

    def test_alibaba(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('d1'))
        board.add_new_piece('Alibaba', Player.WHITE, Pos('d1'))

        alibaba: Piece | None = board.piece_at(Pos('d1'))
        assert alibaba is not None

        self.assertEqual(
            alibaba.legal_moves(),
            set(map(Pos, {'b3', 'd3', 'f3'})),
        )

    def test_alfil(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('c1'))
        board.add_new_piece('Alfil', Player.WHITE, Pos('c1'))

        alfil: Piece | None = board.piece_at(Pos('c1'))
        assert alfil is not None

        self.assertEqual(
            alfil.legal_moves(),
            set(map(Pos, {'a3', 'e3'})),
        )

    def test_dabbaba(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('a1'))
        board.add_new_piece('Dabbaba', Player.WHITE, Pos('a1'))

        dabbaba: Piece | None = board.piece_at(Pos('a1'))
        assert dabbaba is not None

        self.assertEqual(
            dabbaba.legal_moves(),
            set(map(Pos, {'a3'})),
        )

    def test_skip_pieces(self) -> None:
        board = Board.orthodox()

        board.remove_piece_at(Pos('a1'))
        board.remove_piece_at(Pos('c1'))
        board.remove_piece_at(Pos('d1'))
        board.add_new_piece('Skip Rook',   Player.WHITE, Pos('a1'))
        board.add_new_piece('Skip Bishop', Player.WHITE, Pos('c1'))
        board.add_new_piece('Skip Queen',  Player.WHITE, Pos('d1'))

        skip_rook:   Piece | None = board.piece_at(Pos('a1'))
        skip_bishop: Piece | None = board.piece_at(Pos('c1'))
        skip_queen:  Piece | None = board.piece_at(Pos('d1'))
        assert skip_rook   is not None
        assert skip_bishop is not None
        assert skip_queen  is not None

        self.assertEqual(
            skip_rook.legal_moves(),
            set(map(Pos, {'a3', 'a5', 'a7'})),
        )
        self.assertEqual(
            skip_bishop.legal_moves(),
            set(map(Pos, {'a3', 'e3', 'g5'})),
        )
        self.assertEqual(
            skip_queen.legal_moves(),
            set(map(Pos, {'b3', 'd3', 'd5', 'd7', 'f3', 'h5'})),
        )


if __name__ == '__main__':
    ut.main()

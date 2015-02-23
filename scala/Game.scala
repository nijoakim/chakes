/* Copyright 2015 Joakim Nilsson, Kim Albertsson
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

package chakes.game

import akka.actor._

// =====================
// Chakes game exception
// =====================

case class ChakesGameException(msg: String) extends Exception(msg)

abstract class ChakesGameEvent;
abstract class ChakesGameEventFromModel extends ChakesGameEvent;
abstract class ChakesGameEventToModel   extends ChakesGameEvent;

case class ChakesGameStart() extends ChakesGameEvent
case class ChakesGameEnd(winner: List[Int]) extends ChakesGameEvent

case class ChakesGameRegisterView(   view  : chakes.gui.BoardView ) extends ChakesGameEvent
case class ChakesGameRegisterBoard(  board : Board ) extends ChakesGameEvent
case class ChakesGameRegisterActorView(  view  : ActorRef ) extends ChakesGameEvent
case class ChakesGameRegisterActorBoard( board : Board    ) extends ChakesGameEvent

// From Model
case class ChakesGameBoardCreated(   board: Board) extends ChakesGameEventFromModel
case class ChakesGameBoardDestroyed( board: Board) extends ChakesGameEventFromModel

case class ChakesGamePieceCreated(   board: Board, p: Piece, at: (Int, Int)) extends ChakesGameEventFromModel
case class ChakesGamePieceDestroyed( board: Board, p: Piece, at: (Int, Int)) extends ChakesGameEventFromModel

case class ChakesGamePieceMoved(     board: Board, p: Piece, from: (Int, Int), to: (Int, Int)) extends ChakesGameEventFromModel
case class ChakesGameLegalMoves(coordinates: Set[(Int, Int)]) extends ChakesGameEventFromModel

// To Model
case class ChakesGameMovePiece(from: (Int, Int), to: (Int, Int)) extends ChakesGameEventToModel
case class ChakesGameLegalMovesFor(at: (Int, Int)) extends ChakesGameEventToModel

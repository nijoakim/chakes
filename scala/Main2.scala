/* Copyright 2015 Joakim Nilsson
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

// This file is only used for testing

package runtime

import org.luaj.vm2._
import org.luaj.vm2.lib.jse._

import luaj.interface._
import luaj.interface.Implicits._

import chakes.game._

import akka.actor._

object Main2 extends App {
	println("\n***** Non-GUI tests *****\n")
	
	// Define letters as numbers
	val A = 1
	val B = 2
	val C = 3
	val D = 4
	val E = 5
	val F = 6
	val G = 7
	val H = 8
	val I = 9
	val J = 10
	val K = 11
	val L = 12
	val M = 13
	val N = 14
	val O = 15
	val P = 16
	val Q = 17
	val R = 18
	val S = 19
	val T = 20
	val U = 21
	val V = 22
	val W = 23
	val X = 24
	val Y = 25
	val Z = 26
	
	// =====
	// Tests
	// =====
	
	// Run test file
	// JsePlatform.standardGlobals.get("dofile").call(LuaValue.valueOf("lua/games/Chess.lua"))
	
	// Test chess
	{
		val system = ActorSystem("MySystem")
		val boardActor = system.actorOf(Props[BoardActor], name = "board");
		val board = new Board("Chess", List("White", "Black"), boardActor)
		
		board.initGameLogic()
		board.printBoard
		
		// Pawn
		board.movePiece(D, 2, D, 3) // 1-step
		board.movePiece(E, 2, E, 4) // 2-step

		// Knight
		board.movePiece(B, 1, C, 3)

		// Bishop
		println( board.pieces(C, 1).isLegalMove(E, 3) )
		board.movePiece(C, 1, E, 3)

		// Queen
		board.movePiece(D, 1, F, 3) // Diagonal
		board.movePiece(F, 3, F, 7) // Straight

		// King
		board.movePiece(E, 1, C, 1) // Long castling
		board.movePiece(C, 1, B, 1) // Ordinary move

		// Rook
		board.movePiece(D, 1, E, 1)
		
		board.printBoard
	}
}

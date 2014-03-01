/* Copyright 2014 Joakim Nilsson
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

package runtime

import org.luaj.vm2._
import org.luaj.vm2.lib.jse._

import luaj.interface._
import luaj.interface.Implicits._

import chakes.game._

object Main extends App {
	println("\n***** Program started *****\n")
	// Example code
	/*val global = JsePlatform.standardGlobals
	global.get("dofile").call(LuaValue.valueOf("hello.lua"))
	
	val luaPrint = LuajInterface.getFun(global, "printeter")
	val luaAdd = LuajInterface.getFun(global, "add")
	val luaMret = LuajInterface.getFun(global, "mret")
	
	luaPrint(luaAdd(5, 3).arg(2))
	
	luaPrint(1)
	
	luaPrint("huuu", "skabb", "gris")
	
	println(luaMret().arg(2))
	
	//*/
	
	// Board and stuff
	val board = new Board("Chess", List("White", "Black"))
	board.printBoard
	
	//board.movePiece(5, 2, 5, 4)
	//board.movePiece(4, 1, 6, 3)
	
	///* Test castling
	board.movePiece(5, 2, 5, 3)
	board.movePiece(6, 1, 4, 3)
	board.movePiece(7, 1, 8, 3)
	board.movePiece(5, 1, 7, 1)
	
	//println(board.pieces(1,1).name)
	
	board.printBoard
	//*/
	
	/* Capture the king
	board.movePiece(4, 2, 4, 4)
	board.movePiece(5, 7, 5, 5)
	board.movePiece(6, 8, 2, 4)
	board.movePiece(2, 4, 5, 1)
	
	board.printBoard
	//*/
	
	/*
	//board.movePiece(1, 1, 1, 3)
	board.printBoard
	board.movePiece(6, 8, 1, 3)
	board.printBoard
	board.movePiece(2, 1, 1, 3)
	board.printBoard
	board.movePiece(1, 8, 1, 3)
	board.printBoard
	board.movePiece(3, 1, 2, 2)
	board.printBoard//*/
	
	//val moves = board.pieces(1, 1).legalMoves().arg1
	
	//for (i <- 1 to moves.length) println(moves.get(i).get(1).toint.+(64).toChar.toString + moves.get(i).get(2))
}



//luaGlobal.get("dofile").call(LuaValue.valueOf(script))


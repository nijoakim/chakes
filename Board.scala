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

package chakes.game

import org.luaj.vm2._
import org.luaj.vm2.lib.jse._
import org.luaj.vm2.lib._

import luaj.interface._
import luaj.interface.Implicits._

import collection.mutable.HashMap
import scala.util.control.Breaks._

// ============
// Board object
// ============

object Board {
	// Constants
		// Lua values
		private val LuavarSize = "boardSize"
		private val LuavarTypes = "pieceTypes"
		
		// Paths
		private val GamesPath = "rules/games/"
		private val PiecesPath = "rules/pieces/"
		private val ResoursesPath = "rules/resources/"
		
		// Lua file type extension
		private val LuaExt = ".lua"
	
	private def numToAlpha(n: Int) = ('A' + n - 1).toChar
}

// ===========
// Board class
// ===========

/** A grid-based board.
 * 
 *  @constructor Creates a new board with given properties
 *  @param gameName Name of the game which is played on this board
 *  @param playerNames Names of the players who are playing on this board
 */
class Board(val gameName: String, playerNames: Iterable[String]) {
	import Board._
	
	/** Hash map of pieces on the board indexed by position. */
	val pieces = new HashMap[(Int, Int), Piece]
	
	private val players = playerNames.toArray            // Players array
	private val gamePath = GamesPath + gameName + LuaExt // Path to games
	private val globals = JsePlatform.standardGlobals    // Lua globals table
	
	// Dimensions
	var xSize = 0 /** Width of the board. */
	var ySize = 0 /** Height o the board. */
	
	// Define letters as numbers
	for (i <- 1 to 26) {
		val char: String = numToAlpha(i).toString
		globals.set(char, i)
	}
	
	globals.load(new LuaLibChakes)       // Add Chakes library
	globals.get("dofile").call(gamePath) // Run game file
	
	private def isOnBoard(x: Int, y: Int) = (x >= 1 && x <= xSize && y >= 1 && y <= ySize)
	
	private def destroyPiece(x: Int, y: Int): Unit = {
		val pieceMaybe = pieces.get(x, y)
		pieceMaybe match {
			case Some(piece) => {
				piece.onDestroy()
				pieces -= ((piece.x, piece.y): (Int, Int))
			}
			case None => Unit
		}
	}
	
	private def getPieceOrError(x: Int, y: Int): Piece = {
		def throwExc = throw new ChakesGameException("Tried to access piece at empty position, "+ numToAlpha(x) + y +".")
		val piece = pieces.getOrElse((x, y), throwExc)
		if (piece.hidden) throwExc
		piece
	}
	
	/** Prints the board for debugging purposes. */
	def printBoard = {
		for (y <- ySize to 1 by -1; x <- 1 to xSize) {
			print(if (x == 1) y.toString + " " else " ")
			print(pieces.getOrElse((x, y), "."))
			print(if (x == xSize) "\n" else "")
		}
		println(" "+ (for (x <- 1 to xSize) yield (" " + numToAlpha(x))).mkString + "\n")
	}
	
	/** Prints the legal moves for a piece at a given position for debugging purposes.
	  * 
	  * @param x x position of the piece
	  * @param y y position of the piece
	  * @throws ChakesGameException if there is no piece at the given position.
	  */
	def printLegalMoves(x: Int, y: Int) = {
		val moves = getLegalMoves(getPieceOrError(x, y))
		for (y <- ySize to 1 by -1; x <- 1 to xSize) {
			print(if (x == 1) y.toString + " " else " ")
			print(if (moves(x, y)) "x" else ".")
			print(if (x == xSize) "\n" else "")
		}
		println(" "+ (for (x <- 1 to xSize) yield (" " + numToAlpha(x))).mkString + "\n")
	}
	
	/** Returns a hashmap of moves that are legal for a piece to do.
	  * 
	  * @param piece Piece to investigate for legal moves.
	  * @return HashMap indexable by position giving `false` for illegal moves and `true` otherwise. 
	  */ 
	def getLegalMoves(piece: Piece): HashMap[(Int, Int), Boolean] = {
		val moves = piece.legalMoves().arg1.checktable
		val ret = new HashMap[(Int, Int), Boolean]() { override def default(key: (Int, Int)) = false }
		for (i <- 1 to moves.length) {
			val pair = moves.get(i).checktable
			ret += (pair.get(1).checkint, pair.get(2).checkint) -> true
		}
		ret
	}
	
	/** Moves a piece from one position to another, destroying any piece already occupying the final
	  * position and in that case also calling that piece's `onDestroy()` method.
	  * 
	  * @param x1 initial x position of the piece to be moved.
	  * @param y1 initial y position of the piece to be moved.
	  * @param x2 final x position of the piece to be moved.
	  * @param y2 final y position of the piece to be moved.
	  * @throws ChakesGameException if there is no piece at the given position or if the move is illegal
	  */
	def movePiece(x1: Int, y1: Int, x2: Int, y2: Int): Unit = movePiece(x1, y1, x2, y2, true)
	
	private def movePiece(x1: Int, y1: Int, x2: Int, y2: Int, callOnMove: Boolean): Unit = {
		val piece: Piece = getPieceOrError(x1, y1)
		if (!getLegalMoves(piece)(x2, y2)) throw new ChakesGameException("Illegal move. "+ piece.defName +" cannot move from "+ numToAlpha(x1) + y1 +" to "+ numToAlpha(x2) + y2 +".")
		if (callOnMove) piece.onMove(x1, y1, x2, y2)
		destroyPiece(x2, y2)
		pieces += (x2, y2) -> piece
		pieces -= ((x1, y1): (Int, Int))
		piece.x = x2
		piece.y = y2
	}
	
	// ==========================
	// Lua library function class
	// ==========================
	
	// TODO: Document errors?
	// Sets up library
	private class LuaLibChakes() extends OneArgFunction {
		override def call(env: LuaValue) = {
			// Prepare table
			val libFuns: LuaTable = new LuaTable
			env.set("chakes", libFuns)
			env.get("package").get("loaded").set("chakes", libFuns)
			
			// Add library functions
			libFuns.set("setBoardSize",     new LuaLibFun_SetBoardSize)
			libFuns.set("isOnBoard",        new LuaLibFun_IsOnBoard)
			libFuns.set("addPieceDefs",     new LuaLibFun_AddPieceDefs)
			libFuns.set("createPiece",      new LuaLibFun_CreatePiece)
			libFuns.set("removePiece",      new LuaLibFun_RemovePiece)
			libFuns.set("destroyPiece",     new LuaLibFun_DestroyPiece)
			libFuns.set("movePiece",        new LuaLibFun_MovePiece)
			libFuns.set("hidePiece",        new LuaLibFun_HidePiece)
			libFuns.set("unhidePiece",      new LuaLibFun_UnhidePiece)
			libFuns.set("getPiece",         new LuaLibFun_GetPiece)
			libFuns.set("getOwner",         new LuaLibFun_GetOwner)
			libFuns.set("setOwner",         new LuaLibFun_SetOwner)
			libFuns.set("getFreezeTime",    new LuaLibFun_GetFreezeTime)
			libFuns.set("setFreezeTime",    new LuaLibFun_SetFreezeTime)
			libFuns.set("isUnderThreat",    new LuaLibFun_IsUnderThreat)
			
			libFuns
		}
		
		/*
		--- Sets the size of the board.
		 -- @param x x size
		 -- @param y y size
		 function setBoardSize(x, y)
		*/
		class LuaLibFun_SetBoardSize extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				xSize = x.checkint // Set x size
				ySize = y.checkint // Set y size
				for ((_, piece) <- pieces) if (!isOnBoard(piece.x, piece.y)) throw new ChakesGameException("Resize of board resulted in that piece placed at "+ numToAlpha(piece.x) + piece.y +" is no longer placed on the board.")
				LuaValue.NIL
			}
		}
		
		/*
		--- Checks whether position is within the bounds of the board.
		 -- @param x x position
		 -- @param y y position
		 -- @return true if position is on board, false otherwise
		 function isOnBoard(x, y)
		*/
		private class LuaLibFun_IsOnBoard extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = isOnBoard(x.checkint, y.checkint)
		}
		
		/*
		--- Adds piece definition form piece files.
		 -- @param luaPieceNames Table of strings with piece names corresponding to the piece files
		function addPieceDefs(luaPieceNames)
		*/
		private class LuaLibFun_AddPieceDefs extends OneArgFunction {
			override def call(luaPieceNames: LuaValue): LuaValue = {
				val pieceNames = (for (i <- 1 to luaPieceNames.checktable.length) yield luaPieceNames.get(i).checkjstring).toList // Get piece names
				for (pieceName <- pieceNames) globals.get("dofile").call(Board.PiecesPath + pieceName + Board.LuaExt)             // Run piece file for each name
				LuaValue.NIL
			}
		}
		
		// TODO: Check so that the place is empty
		/*
		--- Creates an instance of a piece
		 -- @param x x position of the new piece
		 -- @param y y position of the new piece
		 -- @param name Name of piece
		 -- @param owner Player ID
		 -- @return Piece instance
		function createPiece(x, y, name, owner)
		*/
		private class LuaLibFun_CreatePiece extends FourArgFunction {
			override def call(x: LuaValue, y: LuaValue, name: LuaValue, owner: LuaValue): LuaValue = {
				if (!isOnBoard(x.checkint, y.checkint)) throw new ChakesGameException("Cannot create piece outside board.")
				val piece = new Piece(globals, name.checkjstring, x.toint, y.toint, owner.checkint) // Make new piece
				pieces += (x.toint, y.toint) -> piece                                               // Add piece to Scala
				globals.set(piece.name, globals.get(name).invokemethod("new").arg1)                 // Add piece to Lua through its constructor
				piece.loadMethods                                                                   // Load piece methods
				piece.onCreate(x.toint, y.toint)                                                    // Call piece's onCreate() mehtod
				globals.get(piece.name)                                                             // Return piece instance
			}
		}
		
		/*
		--- Removes piece at given position without calling onDestroy() on it.
		 -- @param x x position of the piece to be removed
		 -- @param y y position of the piece to be removed
		function removePiece(x, y)
		*/
		private class LuaLibFun_RemovePiece extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				getPieceOrError(x.checkint, y.checkint)
				pieces -= ((x.toint, y.toint): (Int, Int))
				LuaValue.NIL
			}
		}
		
		/*
		--- Destroys piece at given position and calls onDestroy() on it.
		 -- @param x x position of the piece to be destroyed
		 -- @param y y position of the piece to be destroyed
		function destroyPiece(x, y)
		*/
		private class LuaLibFun_DestroyPiece extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				getPieceOrError(x.checkint, y.checkint).onDestroy()
				pieces -= ((x.toint, y.toint): (Int, Int))
				LuaValue.NIL
			}
		}
		
		/*
		--- Moves a piece without calling onMove() on it, destroys any piece positioned at the destination and, in that case, calls onDestroy() on it.
		 -- @param x1 Initial x position
		 -- @param y1 Initial y position
		 -- @param x2 Final x position
		 -- @param y2 Final y position
		function movePiece(x1, y1, x2, y2)
		*/
		private class LuaLibFun_MovePiece extends FourArgFunction {
			override def call(x1: LuaValue, y1: LuaValue, x2: LuaValue, y2: LuaValue): LuaValue = {
				if (!isOnBoard(x1.checkint, y1.checkint)) throw new ChakesGameException("Tried to access piece from outside board.")
				getPieceOrError(x1.toint, y1.toint)
				if (!isOnBoard(x2.checkint, y2.checkint)) throw new ChakesGameException("Cannot move piece outside board.")
				movePiece(x1.toint, y1.toint, x2.toint, y2.toint, false)
				LuaValue.NIL
			}
		}
		
		/*
		--- Hides piece at given position.
		 -- @param x x position at where to hide piece
		 -- @param y y position at where to hide piece
		function hidePiece(x, y)
		*/
		private class LuaLibFun_HidePiece extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				val piece = getPieceOrError(x.checkint, y.checkint)
				if (piece.hidden) throw new ChakesGameException("Tried to hide hidden piece at "+ numToAlpha(y.toint) + x.toint + ".")
				else piece.hidden = true
				LuaValue.NIL
			}
		}
		
		/*
		--- Unhides piece at given position.
		 -- @param x x position at where to unhide piece
		 -- @param y y position at where to unhide piece
		function unhidePiece(x, y)
		*/
		private class LuaLibFun_UnhidePiece extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				val piece = pieces.getOrElse((x.checkint, y.checkint), getPieceOrError(x.toint, y.toint))
				if (!piece.hidden) throw new ChakesGameException("Tried to unhide non-hidden piece at "+ numToAlpha(y.toint) + x.toint + ".")
				else piece.hidden = false
				LuaValue.NIL
			}
		}
		
		/*
		--- Gets piece from position.
		 -- @param x position
		 -- @param y position
		 -- @return Piece instance at given position or nil of the position was empty
		function getPiece(x, y)
		*/
		private class LuaLibFun_GetPiece extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				val piece = pieces.getOrElse((x.checkint, y.checkint), return LuaValue.NIL) // Get piece or return nil if no piece
				if (piece.hidden) return LuaValue.NIL                                       // Also return nil for hidden piece
				globals.get(piece.name)                                                     // Return piece
			}
		}
		
		/*
		--- Gets owner from position.
		 -- @param x position
		 -- @param y position
		 -- @return Player ID which owns a piece at the given position
		function getOwner(x, y)
		*/
		private class LuaLibFun_GetOwner extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				getPieceOrError(x.checkint, y.checkint).owner
			}
		}
		
		/*
		--- Sets owner of piece at given position.
		 -- @param x x position at where to set owner
		 -- @param y y position at where to set owner
		 -- @param owner Player ID
		function setOwner(x, y, owner)
		*/
		private class LuaLibFun_SetOwner extends ThreeArgFunction {
			override def call(x: LuaValue, y: LuaValue, owner: LuaValue): LuaValue = {
				getPieceOrError(x.checkint, y.checkint).owner = owner.checkint
				LuaValue.NIL
			}
		}
		
		/*
		--- Gets freeze time of piece at given position.
		 -- @param x x position at where to get freeze time from piece
		 -- @param y y position at where to get freeze time from piece
		 -- @return Freeze time of piece at given position
		function getFreezeTime(x, y)
		*/
		private class LuaLibFun_GetFreezeTime extends TwoArgFunction {
			override def call(x: LuaValue, y: LuaValue): LuaValue = {
				getPieceOrError(x.checkint, y.checkint).freezeTime
			}
		}
		
		/*
		--- Sets freeze time of piece at given position.
		 -- @param x x position at where to set freeze time to piece
		 -- @param y y position at where to set freeze time to piece
		 -- @param freezeTime Freeze time of piece at given position
		function setFreezeTime(x, y)
		*/
		private class LuaLibFun_SetFreezeTime extends ThreeArgFunction {
			override def call(x: LuaValue, y: LuaValue, freezeTime: LuaValue): LuaValue = {
				getPieceOrError(x.checkint, y.checkint).freezeTime = freezeTime.checkdouble
				LuaValue.NIL
			}
		}
		
		/*
		--- Returns whether a given position is under threat.
		 -- @param x x position at where to check for threats
		 -- @param y y position at where to check for threats
		 -- @returns true if a threat was found, false otherwise
		function isUnderThreat(x, y)
		*/
		private class LuaLibFun_IsUnderThreat extends ThreeArgFunction {
			override def call(x: LuaValue, y: LuaValue, owner: LuaValue): LuaValue = {
				x.checkint
				y.checkint
				owner.checkint
				for ((_, piece) <- pieces) {
					if (piece.owner == owner.toint && !piece.hidden && getLegalMoves(piece)(x.toint, y.toint)) return true
				}
				false
			}
		}
	}
}

// ==================================================
// Lua lib function classes for more than 3 arguments
// ==================================================

private abstract class FourArgFunction extends LibFunction {	
	def call(arg1: LuaValue, arg2: LuaValue, arg3: LuaValue, arg4: LuaValue): LuaValue
	override def call = call(LuaValue.NIL, LuaValue.NIL, LuaValue.NIL, LuaValue.NIL)
	override def call(arg: LuaValue) = call(arg, LuaValue.NIL, LuaValue.NIL, LuaValue.NIL)
	override def call(arg1: LuaValue, arg2: LuaValue) = call(arg1, arg2, LuaValue.NIL, LuaValue.NIL)
	override def call(arg1: LuaValue, arg2: LuaValue, arg3: LuaValue) = call(arg1, arg2, arg3, LuaValue.NIL)
	override def invoke(varargs: Varargs) = call(varargs.arg1, varargs.arg(2), varargs.arg(3), varargs.arg(4))
}

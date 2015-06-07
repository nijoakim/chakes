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

import org.luaj.vm2._
import org.luaj.vm2.lib.jse._
import org.luaj.vm2.lib._

import luaj.interface._
import luaj.interface.Implicits._

import collection.mutable.HashMap
import scala.util.control.Breaks._

import akka.actor._

/**
 * Works as a proxy between the model and other parts of the game (gui,
 * network). Thus handles 2-way communication.
 */
class BoardActor extends Actor {
	var board: Board = null;

	var registeredActors: List[ActorRef] = Nil;

	def receive = {

	// CONTROL
		case ChakesGameRegisterActorView(viewActor) => {
			registeredActors ::= viewActor;
		}

		case ChakesGameRegisterBoard(board) => {
			this.board = board;
		}

	// === FROM MODEL
		case msg: ChakesGameEventFromModel => {
			registeredActors.map( x => x.forward(msg) );
		}

	// === TO MODEL
		case ChakesGameStart() => {
			if (board != null) {
				board.initGameLogic();
			}
		}

		case ChakesGameMovePiece(from, to) => {
			board.movePiece(from._1, from._2, to._1, to._2 );
		}

		case ChakesGameLegalMovesFor(at: (Int, Int)) => {
			try {
				val piece = board.getPieceOrError(at._1, at._2);
				val map: scala.collection.mutable.Map[(Int, Int), Boolean]   = board.getLegalMoves(piece);
				registeredActors.map( x => x ! ChakesGameLegalMoves(map.keySet.toSet));
			} catch {
				case e: ChakesGameException => ()
			}
		}
	}

	/**
	 * TODO: This needs to be thought about. The lua part needs to incorporate 
	 * alls like `actor ! Message()` directly but scala code can be wrapped
	 * like ChakesLegalMoves? Which is better?
	 */
}

// ============
// Board object
// ============

object Board {
	// Constants
		// Lua values
		private val LuavarSize = "boardSize"
		private val LuavarTypes = "pieceTypes"
		
		// Paths
		private val GamesPath = "lua/games/"
		private val PiecesPath = "lua/pieces/"
		private val ResoursesPath = "lua/resources/"
		
		// Lua file type extension
		private val LuaFileExt = ".lua"
	
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
class Board(val gameName: String, playerNames: Iterable[String], var actor: ActorRef) {
	import Board._
	
	/** Hash map of pieces on the board indexed by position. */
	val pieces = new HashMap[(Int, Int), Piece]
	
	private val players  = playerNames.toArray                // Players array
	private val gamePath = GamesPath + gameName + LuaFileExt  // Path to games
	private val globals  = JsePlatform.standardGlobals        // Lua globals table
	
	// Dimensions
	var xSize = 0 /** Width of the board. */
	var ySize = 0 /** Height o the board. */
	
	// [Lua] Define letters as numbers
	for (i <- 1 to 26) {
		val char: String = numToAlpha(i).toString
		globals.set(char, i)
	}
	
	globals.load(new LuaLibChakes)       // Add Chakes library
	
	// Temporarily made this public, for easier testing without the GUI
	// private[game] def initGameLogic() {
	def initGameLogic() {
		// Temporary hack to get things to work.
		this.xSize = 8;
		this.ySize = 9;
		actor ! ChakesGameBoardCreated(this);

		globals.get("dofile").call(gamePath) // Run game file
	}
	
	// Returns whether a given position is on board
	private def isOnBoard(x: Int, y: Int): Boolean = (
		(1 <= x && x <= xSize) &&
		(1 <= y && y <= ySize)
	)

	// Destroys a piece at a given position an calls onDestroy() on it
	private def destroyPiece(x: Int, y: Int): Unit = {
		val pieceMaybe = pieces.get(x, y)
		pieceMaybe match {
			case Some(piece) => {
				val at: (Int, Int) = (piece.x, piece.y)
				// Remove piece and call onDestroy() on it
				piece.onDestroy()
				pieces -= at

				actor ! ChakesGamePieceDestroyed(this, piece, at)
			}
			case None => Unit
		}
	}
	
	// Returns the piece at a given position or throws an error if empty
	def getPieceOrError(x: Int, y: Int): Piece = {
		def throwExc = throw new ChakesGameException("Tried to access piece at empty position, "+ numToAlpha(x) + y +".")
		val piece = pieces.getOrElse((x, y), throwExc)
		if (piece.hidden) throwExc // Hidden pieces are not valid
		piece
	}
	
	/** Prints the board. */
	def printBoard = {
		for (y <- ySize to 1 by -1; x <- 1 to xSize) {
			print(if (x == 1) y.toString + " " else " ")
			print(pieces.getOrElse((x, y), "."))
			print(if (x == xSize) "\n" else "")
		}
		println(" "+ (for (x <- 1 to xSize) yield (" " + numToAlpha(x))).mkString + "\n")
	}
	
	/** Prints the legal moves for a piece at a given position.
	  * 
	  * @param x x position of the piece
	  * @param y y position of the piece
	  * @throws ChakesGameException if there is no piece at the given position.
	  */
	def printLegalMoves(x: Int, y: Int) = {
		val moves = getLegalMoves(getPieceOrError(x, y))
		for (y <- ySize to 1 by -1; x <- 1 to xSize) {
			print(if (x == 1) y.toString + " " else " ")
			print(if (moves(x, y)) "x" else pieces.getOrElse((x, y), ".")) // TODO: print "X" for capture
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
		// Get lua table of legal moves
		val movesLuaTable = piece.legalMoves().arg1.checktable
		
		// Iterate over moves and add them to hashmap
		val movesHashmap = new HashMap[(Int, Int), Boolean]() { override def default(key: (Int, Int)) = false }
		for (i <- 1 to movesLuaTable.length) {
			val pair = movesLuaTable.get(i).checktable
			movesHashmap += (pair.get(1).checkint, pair.get(2).checkint) -> true
		}
		
		movesHashmap
	}
	
	/** Moves a piece from one position to another, destroying any piece already occupying the final position and in that case also calling that piece's `onDestroy()` method.
	  * 
	  * @param x1 initial x position of the piece to be moved.
	  * @param y1 initial y position of the piece to be moved.
	  * @param x2 final x position of the piece to be moved.
	  * @param y2 final y position of the piece to be moved.
	  * @throws ChakesGameException if there is no piece at the given position or if the move is illegal
	  */
	def movePiece(x1: Int, y1: Int, x2: Int, y2: Int): Unit = movePiece(x1, y1, x2, y2, true)
	
	// Same as movePiece above, but with extra argument determining whether to call onMove()
	private def movePiece(x1: Int, y1: Int, x2: Int, y2: Int, callOnMove: Boolean): Unit = {
		val piece: Piece = getPieceOrError(x1, y1)
	
		// Throw exeption if illegal move
		if (!getLegalMoves(piece)(x2, y2)) {
			throw new ChakesGameException("Illegal move. "+ piece.defName +" cannot move from "+ numToAlpha(x1) + y1 +" to "+ numToAlpha(x2) + y2 +".")
		}
		
		if (callOnMove) piece.onMove(x1, y1, x2, y2) // Call onMove() if required
		destroyPiece(x2, y2)                         // Destroy eventual piece at new position 
		pieces += (x2, y2) -> piece                  // Put piece at new posion 
		pieces -= ((x1, y1): (Int, Int))             // Remove piece from old position
		
		// Update piece position variables
		piece.x = x2
		piece.y = y2

		// Notify
		actor ! ChakesGamePieceMoved(this, piece, (x1, y1), (x2, y2));
	}
	
	// ======================================
	// Lua library function private sub class
	// ======================================
	
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
			libFuns.set("relocatePiece",    new LuaLibFun_RelocatePiece)
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
				// Update board size
				xSize = x.checkint
				ySize = y.checkint
				
				// Exception if pieces end up outside of board boundary
				for ((_, piece) <- pieces) if (!isOnBoard(piece.x, piece.y)) {
					throw new ChakesGameException(
						"Resize of board resulted in that piece placed at "+
						numToAlpha(piece.x) + piece.y +
						" is no longer placed on the board."
					)
				}
				
				LuaValue.NIL
			}

			actor ! ChakesGameBoardCreated(Board.this)
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
				for (pieceName <- pieceNames) globals.get("dofile").call(Board.PiecesPath + pieceName + Board.LuaFileExt)         // Run piece file for each name
				
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
				// Exception if outside of board
				if (!isOnBoard(x.checkint, y.checkint)) throw new ChakesGameException("Cannot create piece outside of board.")
				
				val piece = new Piece(globals, name.checkjstring, x.toint, y.toint, owner.checkint) // Make new piece
				pieces += (x.toint, y.toint) -> piece                                               // Add piece to Scala
				globals.set(piece.name, globals.get(name).invokemethod("new").arg1)                 // Add piece to Lua 
				piece.loadMethods                                                                   // Load piece's methods
				piece.onCreate(x.toint, y.toint)                                                    // Call onCreate() on piece
				
				actor ! ChakesGamePieceCreated( Board.this, piece, (x.toint,y.toint) );

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
		function relocatePiece(x1, y1, x2, y2)
		*/
		private class LuaLibFun_RelocatePiece extends FourArgFunction {
			override def call(x1: LuaValue, y1: LuaValue, x2: LuaValue, y2: LuaValue): LuaValue = {
				// Exception if doing things outside of board
				if (!isOnBoard(x1.checkint, y1.checkint)) throw new ChakesGameException("Tried to access piece from outside of board.")
				if (!isOnBoard(x2.checkint, y2.checkint)) throw new ChakesGameException("Cannot move piece outside of board.")
				
				// Get and move piece
				getPieceOrError(x1.toint, y1.toint)
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
				if (piece.hidden) throw new ChakesGameException("Tried to hide hidden piece at "+ numToAlpha(y.toint) + x.toint + ".") // Exception if already hidden
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
				if (!piece.hidden) throw new ChakesGameException("Tried to unhide non-hidden piece at "+ numToAlpha(y.toint) + x.toint + ".") // Exception if not hidden
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

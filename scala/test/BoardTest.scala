package chakes.test

import org.luaj.vm2._
import org.luaj.vm2.lib.jse._

import luaj.interface._
import luaj.interface.Implicits._

import chakes.game._

class BoardTest() {
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

	// Run test file
	JsePlatform.standardGlobals.get("dofile").call(LuaValue.valueOf("lua/Test.lua"))
	
	// Test chess
	{
		val board = new Board("Chess", List("White", "Black"))
		
		// Pawn
		board.movePiece(D, 2, D, 3) // 1-step
		board.movePiece(E, 2, E, 4) // 2-step
		
		// Knight
		board.movePiece(B, 1, C, 3)
		
		// Bishop
		board.movePiece(C, 1, E, 3)
		
		// Queen
		board.movePiece(D, 1, F, 3) // Diagonal
		board.movePiece(F, 3, F, 7) // Straight
		
		// King
		board.movePiece(E, 1, C, 1) // Long castling
		board.movePiece(C, 1, B, 1) // Ordinary move
		
		// Rook
		board.movePiece(D, 1, E, 1)
	}
	
	// ===========
	// Other stuff
	// ===========
	
	// Board and stuff
	val board = new Board("Chess", List("White", "Black"))
	board.printBoard
	
	//board.movePiece(5, 2, 5, 4)
	//board.movePiece(4, 1, 6, 3)
	
	///* Test castling
	board.movePiece(E, 2, E, 3)
	board.movePiece(F, 1, D, 3)
	board.movePiece(G, 1, H, 3)
	board.movePiece(E, 1, G, 1)
	
	//println(board.pieces(1,1).name)
	
	board.printBoard
	//*/
	
	/* Capture the king
	board.movePiece(D, 2, D, 4)
	board.movePiece(E, 7, E, 5)
	board.movePiece(F, 8, B, 4)
	board.movePiece(B, 4, E, 1)
	
	board.printBoard
	*/
	
	/*
	//board.movePiece(A, 1, A, 3)
	board.printBoard
	board.movePiece(F, 8, A, 3)
	board.printBoard
	board.movePiece(B, 1, A, 3)
	board.printBoard
	board.movePiece(A, 8, A, 3)
	board.printBoard
	board.movePiece(C, 1, B, 2)
	board.printBoard
	*/
	
	//val moves = board.pieces(1, 1).legalMoves().arg1
	
	//for (i <- 1 to moves.length) println(moves.get(i).get(1).toint.+(64).toChar.toString + moves.get(i).get(2))
}
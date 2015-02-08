/* Copyright 2015 Kim Albertsson
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

package chakes.gui

import scala.collection.mutable.Map
import scala.collection.mutable.HashMap

// GUI stuff
import scala.swing._
import scala.swing.event._
import scala.swing.GridBagPanel._

// Chakes game
import chakes.game._

// class Controller(){
	
// 	// Actions on the view (from either game-model or )
// 	// The controller subscribes to events in the game and translates them for the view to use.
// 	// from view
// 	def showLegalMoves( src: Piece );
// 	// From game-model
// 	def update( p: Piece )

// 	// Actions on the game-model
// 	def move( src: Piece, target: (Int, Int) );
// }
// class View(){
// 	def updateCell( x: Int, y: Int );

// 	def cellSelected()

// }

class ChakesMainFrame extends MainFrame {

	val board = new Board("Chess", "White"::"Black"::Nil)
	
	title = "Chakes Demo GUI"

	// val boardView = new GridPanel(8,8);
	// board.pieces foreach {case (x, y) => (boardView.contents += new Button {text="a"})}
	val boardView = new BoardView(board);

	contents = boardView.boardPanel
	// val cellView = new BoardCellView();
	// cellView.background = java.awt.Color.BLACK;
	// contents = cellView;

}

class BoardCellView( val coordinate  : (Int, Int),
					 var data        : String,
					 labelColour     : java.awt.Color,
					 bgcolor         : java.awt.Color)
extends GridPanel(1,1)
{
	var label = new Label(data);
	label.font = new Font("Sans", java.awt.Font.BOLD, 32)
	if (labelColour != null) {
		label.foreground = labelColour;
	}

	background = bgcolor
	var savedBackgroud : java.awt.Color = bgcolor;

	minimumSize   = new java.awt.Dimension(75,75);
	preferredSize = new java.awt.Dimension(75,75);
	maximumSize   = new java.awt.Dimension(75,75);
	contents += label;

	def select() {
		background = java.awt.Color.BLUE;
	}

	def deselect() {
		background = savedBackgroud;
	}

	def displayLegalMove() {
		background = java.awt.Color.GREEN;
	}
	def undisplayLegalMove() {
		background = savedBackgroud;
	}

	def resetData() {
		label.text = "";
		label.foreground = BoardView.COLOR_PLAYER_0;
	}

	def setData( data: String, owner: Int ) {
		label.text = data;
		label.foreground = if (owner == 1) BoardView.COLOR_PLAYER_1
                      else if (owner == 2) BoardView.COLOR_PLAYER_2
                      else                 null;
	}
}

class BoardCellViewFactory()
{

	/**
	 * Coordinates numbered from lower left corner. Should depend on board type I guess.
	 * @type {[type]}
	 */
	def newCellForCoord( coordinate: (Int, Int), data: String, player: Int ): BoardCellView = {

		val pieceColour = if      (player == 1) BoardView.COLOR_PLAYER_1
		                  else if (player == 2) BoardView.COLOR_PLAYER_2
		                  else                  null; // TODO: Raise exception?

		val (x, y) = coordinate;
		val backgroundColor = if ((x+y) % 2 == 0) BoardView.COLOR_BACK_EVEN
		                      else                BoardView.COLOR_BACK_ODD;
		val cellView        = new BoardCellView( coordinate, data, pieceColour, backgroundColor);
		cellView;
	}

}

object BoardView {
	val COLOR_BACK_ODD  = java.awt.Color.WHITE;
	val COLOR_BACK_EVEN = java.awt.Color.GRAY;

	val COLOR_SELECTED     = java.awt.Color.BLUE
	val COLOR_LEGAL_MOVE   = java.awt.Color.GREEN
	val COLOR_UNDER_THREAT = java.awt.Color.ORANGE

	val COLOR_PLAYER_0 = java.awt.Color.BLACK
	val COLOR_PLAYER_1 = java.awt.Color.RED
	val COLOR_PLAYER_2 = java.awt.Color.CYAN
}

class BoardView( board: Board ) {

	// Data
	val width  = board.xSize;
	val height = board.ySize;
	val size   = width*height;

	var cellSel: BoardCellView = null;
	var legalMoves : Map[(Int, Int), Boolean] = null;

	// Display
	val boardPanel  = new GridBagPanel();
	val constraints = new boardPanel.Constraints
	val cells       = new HashMap[(Int, Int), BoardCellView]();
	val cellFactory = new BoardCellViewFactory();

	def displayLegalMove( moves: Map[(Int, Int), Boolean] ) {
		for ( (coordinate, _) <- moves) { cells(coordinate).displayLegalMove() }
	}

	def clearLegalMoves() {
		for (cell <- cells.values) { cell.undisplayLegalMove() }
		legalMoves = null;
	}

	def deselectSquare() {
		if (cellSel != null) {
			cellSel.deselect();
			clearLegalMoves();
		}
	}

	def selectSquare( cell: BoardCellView) {
		// Select square
		cellSel = cell;
		cellSel.select();

		// Display legal moves
		try { 
			val (x, y) = cellSel.coordinate;
			val piece = board.getPieceOrError(x, y);
			legalMoves = board.getLegalMoves(piece);
			displayLegalMove( legalMoves );
		} catch {
			case e: ChakesGameException => ()
		}	
	}

	def toggleSquare( cell: BoardCellView ) {

		this.deselectSquare();

		if (cellSel == cell) {
			cellSel = null;
			return;
		}

		this.selectSquare( cell );


	}

	def movePiece( to: BoardCellView, from: BoardCellView ) {
		val (fromX, fromY) = from.coordinate;
		val (toX    , toY) = to.coordinate;

		try {
			val piece = board.getPieceOrError(fromX, fromY);
			board.movePiece( fromX, fromY, toX, toY );
		
			from.resetData();
			to.setData( piece.toString, piece.owner );
		} catch {
		  case e: ChakesGameException => println( e.getMessage() );
		}
}

	// Initialise memebers
	for ( iWidth <- 1 to width; iHeight <- 1 to height ) {
		val piece: Piece = try { 
				board.getPieceOrError(iWidth, iHeight);
			} catch {
				case e: ChakesGameException => null
			}
		val data  = if (piece != null) (piece.toString()) else ("");
		val owner = if (piece != null) (piece.owner)      else (-1);
		val currentCellCoordinate = (iWidth, iHeight);

		val cell = cellFactory.newCellForCoord( currentCellCoordinate, data, owner );
		cells(currentCellCoordinate) = cell;

		cell.listenTo(cell.mouse.clicks)
		cell.reactions += {
			case e: MousePressed => {
				println("You clicked: " + cell.coordinate);

				// If clicked square is a legal move, perform move and deselect instead of select.
				if (legalMoves != null && legalMoves.getOrElse(cell.coordinate, false)) {
					movePiece( cell, cellSel );
					deselectSquare();
				} else {
					toggleSquare( cell );
				}
			}
		}

		// Layout
		constraints.gridx = iWidth;
		constraints.gridy = height-iHeight;
		constraints.weightx = 1.0;
		constraints.weighty = 1.0;
		constraints.fill  = Fill.Both;
		boardPanel.layout( cell ) = constraints;
	}


}
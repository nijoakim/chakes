package chakes.gui

import scala.collection.mutable.Map

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

class BoardCellView(data_in : String, labelColour: java.awt.Color, bgcolor: java.awt.Color ) extends GridPanel(1,1) {

	var data = data_in;
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
		savedBackgroud = background;
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
}

class BoardCellViewFactory() {

	/**
	 * Coordinates numbered from lower left corner. Should depend on board type I guess.
	 * @type {[type]}
	 */
	def newCellForCoord( x: Int, y: Int, data: String, player: Int ): BoardCellView = {

		val pieceColour = if      (player == 1) BoardView.COLOR_PLAYER_1
		                  else if (player == 2) BoardView.COLOR_PLAYER_2
		                  else                  null; // TODO: Raise exception?

		val backgroundColor = if ((x+y) % 2 == 0) BoardView.COLOR_BACK_EVEN
		                      else                BoardView.COLOR_BACK_ODD;
		val cellView        = new BoardCellView(data, pieceColour, backgroundColor);
		cellView;
	}

}

object BoardView {
	val COLOR_BACK_ODD  = java.awt.Color.WHITE;
	val COLOR_BACK_EVEN = java.awt.Color.GRAY;

	val COLOR_SELECTED     = java.awt.Color.BLUE
	val COLOR_LEGAL_MOVE   = java.awt.Color.GREEN
	val COLOR_UNDER_THREAT = java.awt.Color.ORANGE

	val COLOR_PLAYER_1 = java.awt.Color.RED
	val COLOR_PLAYER_2 = java.awt.Color.CYAN
}

class BoardView( board: Board ) {

	// Data
	val width  = board.xSize;
	val height = board.ySize;
	val size   = width*height;

	var cellSel: BoardCellView = null;
	var cellX  : Int = -1; // TODO: var cellCoord: (Int, Int) = null;
	var cellY  : Int = -1;
	var legalMoves : Map[(Int, Int), Boolean] = null;

	// Display
	val boardPanel  = new GridBagPanel();
	val constraints = new boardPanel.Constraints
	val cells       = new Array[BoardCellView](size);
	val cellFactory = new BoardCellViewFactory();

	def displayLegalMove( moves: Map[(Int, Int), Boolean] ) {
		for ( ((x, y), _) <- moves) {
			val index = (x-1) + width*(y-1)
			cells(index).displayLegalMove()
		}
	}

	def clearLegalMoves() {
		for ( x <- 0 until width; y <- 0 until height) {
			val index = (x) + width*(y)
			cells(index).undisplayLegalMove()
		}
	}

	def selectSquare( sqCoord: (Int, Int), cell: BoardCellView ) {

		val (x, y) = sqCoord;

		if (cellSel != null) {
			cellSel.deselect();
			clearLegalMoves();
		}

		cellSel = cell;
		cellSel.select();
		cellX = x;
		cellY = y;

		// Display legal moves
		// TODO: Trigger on square select
		try { 
			val piece = board.getPieceOrError(x, y);
			legalMoves = board.getLegalMoves(piece);
			displayLegalMove( legalMoves );
		} catch {
			case e: ChakesGameException => ()
		}	
	}

	// Initialise memebers
	for ( iWidth <- 0 until width; iHeight <- 0 until height ) {
		val piece: Piece = try { 
				board.getPieceOrError(iWidth+1, iHeight+1);
			} catch {
				case e: ChakesGameException => null
			}
		val data  = if (piece != null) (piece.toString()) else ("");
		val owner = if (piece != null) (piece.owner) else (-1);
		val cell = cellFactory.newCellForCoord( iWidth, iHeight, data, owner );
		cells(iWidth + width*iHeight) = cell;

		cell.listenTo(cell.mouse.clicks)
		cell.reactions += {
			case e: MousePressed => {
				/*
				 * TODO: Instead of generating one function per cell. Generate a call to coordinating function.
				 */
				println("User clicked: (" + iWidth + ", " + iHeight + ")");

				// If clicked square is a legal move, perform move and deselect instead of select.
				val point = (iWidth+1, iHeight+1)
				val index = iWidth + width*iHeight;
				val index2 = cellX-1 + width*(cellY-1);
				if (legalMoves != null && legalMoves.getOrElse(point, false)) {
					try {
						val piece = board.getPieceOrError(cellX, cellY);
						board.movePiece( cellX, cellY, iWidth+1, iHeight+1 );
						cells( index2 ).label.text = "";
						cells( index2 ).label.foreground = java.awt.Color.BLACK;
						cells( index  ).label.text = piece.toString();
						cells( index  ).label.foreground = if      (piece.owner == 1) java.awt.Color.RED
		                                                else if (piece.owner == 2) java.awt.Color.ORANGE
		                                                else                  null;

						if (cellSel != null) {
							cellSel.deselect();
							cellX = -1;
							cellY = -1;
							clearLegalMoves();
						}
						legalMoves = null;
					} catch {
					  case e: Exception => println("Tried to move non-existing piece at (" + iWidth + "," + iHeight + ")");
					}
				} else {
					selectSquare( (iWidth+1, iHeight+1), cell );
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
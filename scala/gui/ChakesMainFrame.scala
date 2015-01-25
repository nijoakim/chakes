package chakes.gui

import scala.collection.mutable.Map

// GUI stuff
import scala.swing._
import scala.swing.event._
import scala.swing.GridBagPanel._

// Chakes game
import chakes.game._

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

class BoardCellView(data_in : String, labelColour: java.awt.Color) extends GridPanel(1,1) {

	var data = data_in;
	var label = new Label(data);
	label.font = new Font("Sans", java.awt.Font.BOLD, 32)
	if (labelColour != null) {
		label.foreground = labelColour;
	}

	var savedBackgroud : java.awt.Color = null;
	var savedBackgroud2: java.awt.Color = null;

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
		savedBackgroud2 = background;
		background = java.awt.Color.GREEN;
	}
	def undisplayLegalMove() {
		background = savedBackgroud2;
	}
}

class BoardCellViewFactory() {

	val backgroundOdd  = java.awt.Color.WHITE;
	val backgroundEven = java.awt.Color.GRAY;

	/**
	 * Coordinates numbered from lower left corner. Should depend on board type I guess.
	 * @type {[type]}
	 */
	def newCellForCoord( x: Int, y: Int, data: String, player: Int ): BoardCellView = {

		val pieceColour = if      (player == 1) java.awt.Color.RED
		                  else if (player == 2) java.awt.Color.ORANGE
		                  else                  null;

		val backgroundColor = if ((x+y) % 2 == 0) backgroundEven else backgroundOdd;
		val cellView        = new BoardCellView(data, pieceColour);
		cellView.background = backgroundColor;
		cellView;
	}

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
						cells(index).label.text = piece.toString();
						cells(index).label.foreground = if      (piece.owner == 1) java.awt.Color.RED
		                                                else if (piece.owner == 2) java.awt.Color.ORANGE
		                                                else                  null;

						if (cellSel != null) {
							cellSel.deselect();
							cellX = -1;
							cellY = -1;
							for ( ((x, y), _) <- legalMoves) {
								val index = (x-1) + width*(y-1)
								cells(index).undisplayLegalMove()
							}
						}
						legalMoves = null;
					} catch {
					  case e: Exception => println("Tried to move non-existing piece at (" + iWidth + "," + iHeight + ")");
					}
				} else {
					// Square selection
					if (cellSel != null) {
						cellSel.deselect();
						cellX = -1;
						cellY = -1;
						if (legalMoves != null) {
							for ( ((x, y), _) <- legalMoves) {
								val index = (x-1) + width*(y-1)
								cells(index).undisplayLegalMove()
							}
						}
					}
					cellSel = cell;
					cellSel.select();
					cellX = iWidth+1;
					cellY = iHeight+1;

					// Display legal moves
					// TODO: Trigger on square select
					try { 
						val piece = board.getPieceOrError(iWidth+1, iHeight+1);
						legalMoves = board.getLegalMoves(piece);
						for ( ((x, y), _) <- legalMoves) {
							val index = (x-1) + width*(y-1)
							cells(index).displayLegalMove()
						}
					} catch {
						case e: ChakesGameException => ()
					}		
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
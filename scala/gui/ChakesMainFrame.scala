package chakes.gui

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

class BoardCellView(data : String) extends GridPanel(1,1) {

	var savedBackgroud: java.awt.Color = null;

	preferredSize =  new java.awt.Dimension(75,75);
	contents += new Label(data);

	def select() {
		savedBackgroud = background;
		background = java.awt.Color.BLUE;
	}

	def deselect() {
		background = savedBackgroud;
	}
}

class BoardCellViewFactory() {

	val backgroundOdd  = java.awt.Color.WHITE;
	val backgroundEven = java.awt.Color.GRAY;

	/**
	 * Coordinates numbered from lower left corner. Should depend on board type I guess.
	 * @type {[type]}
	 */
	def newCellForCoord( x: Int, y: Int, data: String ): BoardCellView = {

		val backgroundColor = if ((x+y) % 2 == 0) backgroundEven else backgroundOdd;
		val cellView        = new BoardCellView(data);
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

	// Display
	val boardPanel  = new GridBagPanel();
	val constraints = new boardPanel.Constraints
	val cells       = new Array[BoardCellView](size);
	val cellFactory = new BoardCellViewFactory();

	// Initialise memebers
	for ( iWidth <- 0 until width; iHeight <- 0 until height ) {
		val data : String = try { 
				board.getPieceOrError(iWidth+1, iHeight+1).toString();
			} catch {
				case e: ChakesGameException => ""
			}

		val cell = cellFactory.newCellForCoord( iWidth, iHeight, data );
		cells(iWidth + width*iHeight) = cell;

		cell.listenTo(cell.mouse.clicks)
		cell.reactions += {
			case e: MousePressed => {
				println("User clicked: (" + iWidth + ", " + iHeight + ")");
				
				if (cellSel != null) { cellSel.deselect(); }
				cellSel = cell;
				cellSel.select();
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
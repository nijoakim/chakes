package chakes.gui

// GUI stuff
import swing._

// Chakes game
import chakes.game._

class ChakesMainFrame extends MainFrame {

	val board = new Board("Chess", "White"::"Black"::Nil)
	
	title = "Chakes Demo GUI"

	val boardView = new GridPanel(8,8);

	board.pieces foreach {case (x, y) => (boardView.contents += new Button {text="a"})}

	contents = { boardView }
}
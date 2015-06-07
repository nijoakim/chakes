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
import javax.swing.Icon
import javax.swing.ImageIcon

import java.io.File

// Actor
import akka.actor._

// Chakes game
import chakes.game._

class ChakesMainFrame extends MainFrame {

	val system = ActorSystem("MySystem")
	val viewActor   = system.actorOf(Props[BoardViewActor], name="boardView");
	val boardActor  = system.actorOf(Props[BoardActor]    , name="board");

	// Must be initialised before Board
	val boardView = new BoardView(boardActor);
	viewActor ! ChakesGameRegisterView(boardView);

	// Must be initialised after BoardView
	val board = new Board("Chess", "White"::"Black"::Nil, boardActor)
	boardActor ! ChakesGameRegisterActorView(viewActor);
	boardActor ! ChakesGameRegisterBoard(board);
	
	boardActor ! ChakesGameStart();
	
	title = "Chakes Demo GUI"

	contents = boardView
}

class BoardCellView( val coordinate  : (Int, Int),
					 bgcolor         : java.awt.Color)
extends GridPanel(1,1)
{
	var isLegalMove: Boolean = false;
	var label = new Label();

	background = bgcolor;
	var savedBackground = bgcolor;

	minimumSize   = new java.awt.Dimension(96,96);
	preferredSize = new java.awt.Dimension(96,96);
	maximumSize   = new java.awt.Dimension(96,96);
	contents += label;

	def select() {
		savedBackground = background;
		background = java.awt.Color.BLUE;
	}

	def deselect() {
		background = savedBackground;
	}

	def displayLegalMove() {
		// TODO: Convert to state machine
		savedBackground = background;
		background = java.awt.Color.GREEN;
		isLegalMove = true;
	}
	def undisplayLegalMove() {
		background = savedBackground;
		isLegalMove = false;
	}

	def resetData() {
		label.icon = null;
	}

	def setData( data: Icon ) {
		label.icon = data
	}
}

class BoardCellViewFactory()
{

	/**
	 * Coordinates numbered from lower left corner. Should depend on board type I guess.
	 * @type {[type]} // FIXME: Not a valid tag
	 */
	def newCellForCoord( coordinate: (Int, Int) ): BoardCellView = {

		val (x, y) = coordinate;
		val backgroundColor = if ((x+y) % 2 == 0) BoardView.COLOR_BACK_EVEN
		                      else                BoardView.COLOR_BACK_ODD;
		val cellView        = new BoardCellView( coordinate, backgroundColor);
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

	def getColorForPlayer(player: Int): java.awt.Color = {
		player match {
			case 0 => COLOR_PLAYER_0;
			case 1 => COLOR_PLAYER_1;
			case 2 => COLOR_PLAYER_2;
		}
	}
}

class BoardViewActor extends Actor {
	var view: BoardView = null;

	def receive = {
		case ChakesGameRegisterView(boardView) => {
			view = boardView;
		}

		case ChakesGameBoardCreated(board: Board) => {
			view.initialise(board.xSize, board.ySize)
		}

		case ChakesGameBoardDestroyed(board: Board) => {
			// TODO: Dispose view
			view = null;
		}

		case ChakesGamePieceCreated(board, piece, coord) => {
			val cell = view.cells(coord);

			// TODO: Should be soft-coded.
			val sprite = view.getIcon(piece);
			cell.setData(sprite);
			
		}

		case ChakesGamePieceDestroyed(board: Board, p: Piece, at: (Int, Int)) => {

		}

		case ChakesGamePieceMoved(board: Board, piece: Piece, from: (Int, Int), to: (Int, Int)) => {
			val cellFrom = view.cells(from);
			val cellTo   = view.cells(to);
			view.movePiece(piece, cellFrom, cellTo);
		}

		case ChakesGameLegalMoves(coordinates: Set[(Int,Int)]) => {
			view.displayLegalMove( coordinates );
		}

		// TODO: Default case...
	}
}

class BoardView(val boardActor: ActorRef) extends FlowPanel {

	var cellSel: BoardCellView = null;
	var legalMoves : Map[(Int, Int), Boolean] = null;

	// Display
	val boardPanel  = new GridBagPanel();
	val constraints = new boardPanel.Constraints
	val cells       = new HashMap[(Int, Int), BoardCellView]();
	val cellFactory = new BoardCellViewFactory();

	val icons = new HashMap[String, Icon]();

	contents += boardPanel;

	private def loadIcon( resourceIdentifier: String ): Icon = {

		val basePathForResources = "./resources/";
		val pathExtension        = ".png";
		val path = basePathForResources + resourceIdentifier + pathExtension

		val icon = new ImageIcon(path);
		return icon;
	}

	def getIcon(piece: Piece): Icon = {

		val ownerString      = if (piece.owner == 1) "white" else "black";
		val resourceFolder   = piece.defName.toLowerCase();
		val resourceFilename = ownerString + "_" + piece.defName.toLowerCase();
		val resourceIdentifier: String = resourceFolder + "/" + resourceFilename;

		if ( ! icons.contains(resourceIdentifier) ) {
			icons += resourceIdentifier -> loadIcon(resourceIdentifier);
		}

		val icon = icons.get(resourceIdentifier);
		icon match {
			case Some(value: Icon) => return value;
			case _                 => throw new ChakesGameException("Could not find resource: " + resourceIdentifier);
		}
	}

	def displayLegalMove( moves: Set[(Int, Int)] ) {
		for (coordinate <- moves) { cells(coordinate).displayLegalMove() }
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

		boardActor ! ChakesGameLegalMovesFor(cellSel.coordinate);
	}

	def toggleSquare( cell: BoardCellView ) {

		this.deselectSquare();

		if (cellSel == cell) {
			cellSel = null;
			return;
		}

		this.selectSquare( cell );
	}

	def movePiece( piece: Piece, from: BoardCellView, to: BoardCellView ) {
		val (fromX, fromY) = from.coordinate;
		val (toX    , toY) = to.coordinate;

		from.resetData();

		// TODO: Should be soft-coded.
		// TODO: Owners should be soft-coded somewhere.
		val sprite = getIcon(piece);
		to.setData(sprite);
	}

	def initialise(width: Int, height: Int) {
		// Initialise memebers
		for ( iWidth <- 1 to width; iHeight <- 1 to height ) {
			// val piece: Piece = try { 
			// 		board.getPieceOrError(iWidth, iHeight);
			// 	} catch {
			// 		case e: ChakesGameException => null
			// 	}
			// val data  = if (piece != null) (piece.toString()) else ("");
			// val owner = if (piece != null) (piece.owner)      else (-1);
			val currentCellCoordinate = (iWidth, iHeight);

			val cell = cellFactory.newCellForCoord( currentCellCoordinate );
			cells(currentCellCoordinate) = cell;

			cell.listenTo(cell.mouse.clicks)
			cell.reactions += {
				case e: MousePressed => {
					println("You clicked: " + cell.coordinate);

					// If clicked square is a legal move, perform move and deselect instead of select.
					if (cell.isLegalMove) {
						// movePiece( cell, cellSel );
						boardActor ! ChakesGameMovePiece(cellSel.coordinate, cell.coordinate);
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

}

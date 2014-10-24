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

// ======================
// Piece signleton object
// ======================

object Piece {
	private val ids = new HashMap[String, Int]
	private def getNextId(name: String): Int = {
		val id = ids.getOrElse(name, 0)
		ids.update(name, id + 1)
		id
	}
}

// ===========
// Piece class
// ===========

/** A piece which can be attached to a board
 * 
 *  @constructor Creates a new piece with given properties
 *  @param globals Lua table to attach this piece to
 *  @param defName This piece's declared name
 *  @param x initial x position of the piece
 *  @param y initial y position of the piece
 *  @param owner This piece's owner
 */
class Piece(val globals: LuaTable, val defName: String, var x: Int, var y: Int, var owner: Int) {
	/** Time until this piece is no longer frozen. */
	var freezeTime: Double = 0
	
	private val id = Piece.getNextId(defName)
	private[game] val name: String = "chakes." + defName + id
	private[game] var hidden: Boolean = false
	
	override def toString = symbol().tojstring take 1
	
	// Lua methods
	private[game] var constructor: (LuaValue*) => Varargs = null
	private[game] var symbol: (LuaValue*) => Varargs = null
	private[game] var legalMoves: () => Varargs = null
	private[game] var onMove: (LuaValue*) => Varargs = null
	private[game] var onCreate: (LuaValue*) => Varargs = null
	private[game] var onDestroy: (LuaValue*) => Varargs = null
	
	// Loads the Lua methods
	private[game] def loadMethods() = {
		val legalMovesVarargs: (LuaValue*) => Varargs = LuajInterface.getMethod(globals, name, "legalMoves")
		legalMoves = () => legalMovesVarargs(x, y) // Always call with position arguments
		
		constructor = 	LuajInterface.getMethod(globals, name, "new")
		symbol = 		LuajInterface.getMethod(globals, name, "symbol")
		onMove = 		LuajInterface.getMethod(globals, name, "onMove")
		onCreate = 		LuajInterface.getMethod(globals, name, "onCreate")
		onDestroy = 	LuajInterface.getMethod(globals, name, "onDestroy")
	}
}

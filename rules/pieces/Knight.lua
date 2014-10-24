--[[ Copyright 2014 Joakim Nilsson
     
     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.
     
     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.
     
     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.
]]

Knight = {}

function Knight:new()
	return table.copy(Knight)
end

function Knight:symbol(x, y) return 'k' end

function Knight:legalMoves(x, y)
	local moves = {}
	addLegalMovesDelta(moves, x, y,  1,  2, 1)
	addLegalMovesDelta(moves, x, y,  2,  1, 1)
	addLegalMovesDelta(moves, x, y,  1, -2, 1)
	addLegalMovesDelta(moves, x, y,  2, -1, 1)
	addLegalMovesDelta(moves, x, y, -1,  2, 1)
	addLegalMovesDelta(moves, x, y, -2,  1, 1)
	addLegalMovesDelta(moves, x, y, -1, -2, 1)
	addLegalMovesDelta(moves, x, y, -2, -1, 1)
	return moves
end

function Knight:onMove(x1, y1, x2, y2)
	return
end

function Knight:onCreate(x, y)
	return
end

function Knight: onDestroy()
	print("Njyhyhyhyhy!")
	return
end

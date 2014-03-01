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

Pawn = {hasMoved = false; dy = 0}

function Pawn:new()
	return table.copy(Pawn)
end

function Pawn:symbol(x, y) return 'o' end

function Pawn:legalMoves(x, y)
	local moves = {}
	
	-- Non-capture move
	if not chakes.getPiece(x, y + self.dy) then 
		table.insert(moves, {x, y + self.dy}) 
	end
	
	-- 2 step move
	if not self.hasMoved and not chakes.getPiece(x, y + self.dy * 2) then
		table.insert(moves, {x, y + self.dy * 2})
	end
	
	-- Capture move right
	if chakes.getPiece(x + 1, y + self.dy) and chakes.getOwner(x + 1, y + self.dy) ~= chakes.getOwner(x, y) then
		table.insert(moves, {x + 1, y + self.dy})
	end
	
	-- Capture move left
	if chakes.getPiece(x - 1, y + self.dy) and chakes.getOwner(x - 1, y + self.dy) ~= chakes.getOwner(x, y) then
		table.insert(moves, {x - 1, y + self.dy})
	end
	
	-- TODO: en passant
	-- TODO: promote
	
	return moves
end

function Pawn:onMove(x1, y1, x2, y2)
	self.hasMoved = true
	return
end

function Pawn:onCreate(x, y)
	if chakes.getOwner(x, y) == 1 then
		self.dy = 1
	else
		self.dy = -1
	end
	return
end

function Pawn: onDestroy()
	print("Bouuuu")
	return
end


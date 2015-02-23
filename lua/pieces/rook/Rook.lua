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

Rook = {hasMoved = false}

function Rook:new()
	return table.copy(self)
end

function Rook:symbol(x, y) return 'r' end

function Rook:legalMoves(x, y)
	local moves = {}
	
	for i = -1, 1 do
		for j = -1, 1 do
			if i == 0 or j == 0 then
				addLegalMovesDelta(moves, x, y, i, j)
			end
		end
	end
	
	return moves
end

function Rook:onMove(x1, y1, x2, y2)
	self.hasMoved = true
	return
end

function Rook:onCreate(x, y)
	return
end

function Rook: onDestroy()
	print("AAAAAAAH!")
	return
end

function Rook:getResources()
	-- Define piece image paths
	black = "lua/pieces/rook/black_rook.png"
	white = "lua/pieces/rook/white_rook.png"

	-- Bundle all resourses
	res = {}
	res["blackSprite"] = black
	res["whiteSprite"] = white

	return res
end

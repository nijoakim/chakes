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

Bishop = {}

function Bishop:new()
	return table.copy(Bishop)
end

function Bishop:symbol(x, y) return 'b' end

function Bishop:legalMoves(x, y)
	local moves = {}
	
	for i = -1, 1, 2 do
		for j = -1, 1, 2 do
			addLegalMovesDelta(moves, x, y, i, j)
		end
	end
	
	return moves
end

function Bishop:onMove(x1, y1, x2, y2)
	return
end

function Bishop:onCreate(x, y)
	return
end

function Bishop: onDestroy()
	print("Halleluja!")
	return
end

function Bishop:getResources()
	-- Define piece image paths
	black = "lua/pieces/bishop/black_bishop.png"
	white = "lua/pieces/bishop/white_bishop.png"

	-- Bundle all resourses
	res = {}
	res["blackSprite"] = black
	res["whiteSprite"] = white
	
	return res
end

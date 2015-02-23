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

Queen = {}

function Queen:new()
	return table.copy(Queen)
end

function Queen:symbol(x, y) return 'Q' end

function Queen:legalMoves(x, y)
	local moves = {}
	
	for i = -1, 1 do
		for j = -1, 1 do
			if i ~= 0 or j ~= 0 then
				addLegalMovesDelta(moves, x, y, i, j)
			end
		end
	end
	
	return moves
end

function Queen:onMove(x1, y1, x2, y2)
	return
end

function Queen:onCreate(x, y)
	return
end

function Queen: onDestroy()
	print("Ni skjuter som kratter")
	return
end

function Queen:getResources()
	-- Define piece image paths
	black = "lua/pieces/queen/black_queen.png"
	white = "lua/pieces/queen/white_queen.png"

	-- Bundle all resourses
	res = {}
	res["blackSprite"] = black
	res["whiteSprite"] = white

	return res
end
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

-- ================
-- Helper functions
-- ================

-- Copies a table -- TODO: Move to 'util'/'misc'-like global file
function table.copy(t)
	local u = {}
	for k, v in pairs(t) do u[k] = v end
	return setmetatable(u, getmetatable(t))
end

-- Returns the sign of a number
function math.signum(x)
	if x > 0 then return 1
	elseif x < 0 then return -1
	else return 0 end
end

-- Legal moves helper function
function addLegalMovesDelta(t, x, y, dx, dy, range)
	range = range or -1           -- Range default is infinity
	if range == 0 then return end -- If range is exceeded, abort
	
	-- If this is the first call in the recursion, get owner of piece in global scope
	local knewOwner = false
	if owner == nil then
		owner = chakes.getOwner(x, y)
		knewOwner = true
	end
	
	-- Add position recursively
	x = x + dx
	y = y + dy
	if chakes.isOnBoard(x, y) then
		if chakes.getPiece(x, y) == nil then
			table.insert(t, {x, y})
			addLegalMovesDelta(t, x, y, dx, dy, range - 1)
		else
			if chakes.getOwner(x, y) ~= owner then table.insert(t, {x, y}) end
		end
	end
	
	-- Thrash global owner variable
	if knewOwner then owner = nil end
	
	return
end

-- ============
-- Set up board
-- ============

-- Misc.
chakes.setBoardSize(8, 8)
chakes.addPieceDefs({"Rook", "Knight", "Bishop", "Queen", "King", "Pawn"})

-- Create pieces

chakes.createPiece(A, 1, "Rook", 1)
chakes.createPiece(H, 1, "Rook", 1)
chakes.createPiece(A, 8, "Rook", 2)
chakes.createPiece(H, 8, "Rook", 2)

chakes.createPiece(B, 1, "Knight", 1)
chakes.createPiece(G, 1, "Knight", 1)
chakes.createPiece(B, 8, "Knight", 2)
chakes.createPiece(G, 8, "Knight", 2)

chakes.createPiece(C, 1, "Bishop", 1)
chakes.createPiece(F, 1, "Bishop", 1)
chakes.createPiece(C, 8, "Bishop", 2)
chakes.createPiece(F, 8, "Bishop", 2)

chakes.createPiece(D, 1, "Queen", 1)
chakes.createPiece(D, 8, "Queen", 2)

chakes.createPiece(E, 1, "King", 1)
chakes.createPiece(E, 8, "King", 2)

for i = A, H do chakes.createPiece(i, 2, "Pawn", 1) end
for i = A, H do chakes.createPiece(i, 7, "Pawn", 2) end



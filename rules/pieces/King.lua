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

King = {hasMoved = false}

function King:new()
	return table.copy(King)
end

function King:symbol(x, y) return 'K' end

function King:legalMoves(x, y)
	local moves = {}
	local oppOwner = 3 - chakes.getOwner(x, y)
	local rook
	
	-- Standard moves
	for i = -1, 1 do
		for j = -1, 1 do
			if i ~= 0 or j ~= 0 then
				addLegalMovesDelta(moves, x, y, i, j, 1)
			end
		end
	end
	
	-- Checks whether a certain position is empty and not under threat if moves
	local function isEmptyAndNotUnderThreatIfMove(xx, yy)
		chakes.hidePiece(x, y)
		
		if chakes.getPiece(xx, yy) then
			chakes.unhidePiece(x, y)
			return false
		end
		
		local ret = not chakes.isUnderThreat(xx, yy, oppOwner)
		chakes.unhidePiece(x, y)
		return ret
	end
	
	-- Short castling
	rook = chakes.getPiece(x + 3, y)
	if not self.hasMoved
	and rook
	and rook:symbol() == 'r'
	and not rook.hasMoved
	and isEmptyAndNotUnderThreatIfMove(x, y)
	and isEmptyAndNotUnderThreatIfMove(x + 1, y)
	and isEmptyAndNotUnderThreatIfMove(x + 2, y)
	then
		table.insert(moves, {x + 2, y})
	end
	
	-- Long castling
	rook = chakes.getPiece(x - 4, y)
	if not self.hasMoved
	and rook
	and rook:symbol() == 'r'
	and not rook.hasMoved
	and isEmptyAndNotUnderThreatIfMove(x, y)
	and isEmptyAndNotUnderThreatIfMove(x - 1, y)
	and isEmptyAndNotUnderThreatIfMove(x - 2, y)
	and isEmptyAndNotUnderThreatIfMove(x - 3, y)
	then
		table.insert(moves, {x - 2, y})
	end	
	
	-- Remove moves which would put the king under threat
	local moveRemoveList = {}
	chakes.hidePiece(x, y)
	for i, move in pairs(moves) do
		if chakes.isUnderThreat(move[1], move[2], oppOwner) then
			table.insert(moveRemoveList, i)
		end
	end
	chakes.unhidePiece(x, y)
	while moveRemoveList[1] do
		table.remove(moves, moveRemoveList[1])
		table.remove(moveRemoveList, 1)
	end
	
	return moves
end

function King:onMove(x1, y1, x2, y2)
	local diff = x2 - x1
	if diff ==  2 then chakes.relocatePiece(H, 1, F, 1); chakes.getPiece(F, 1):onMove(H, 1, F, 1) end -- Short castling
	if diff == -2 then chakes.relocatePiece(A, 1, D, 1); chakes.getPiece(D, 1):onMove(A, 1, D, 1) end -- Long castling
	self.hasMoved = true
	return
end

function King:onCreate(x, y)
	return
end

function King: onDestroy()
	print("The king is dead! Long live the king!")
	print("The king is dead! Long live the king!")
	print("The king is dead! Long live the king!")
	print("The king is dead! Long live the king!")
	print("The king is dead! Long live the king!")
	return
end

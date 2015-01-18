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

-- TODO: LuaDoc?

-- Copies a table
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



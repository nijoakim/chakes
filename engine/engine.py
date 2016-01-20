# Copyright 2016 Joakim Nilsson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class _board:
	def __init__(self):
		self.pieces = {}

	def _getPiece(self, coord):
		return self.pieces[coord] if coord in self.pieces else None

	def _createPiece(self, piece, coord):
		self.pieces[coord] = piece

	# TODO: num should be a string
	def special(self, num, coord):
		raise NotImplementedError("Implement please!")

class _Piece:
	def canMove(self, coord):
		raise NotImplementedError("Implement please!")

	def __str__(self):
		raise NotImplementedError("Implement please!")

class TicTacToe(_board):
	def special(self, num, coord):
		if not self._getPiece(coord):
			self._createPiece(Tic(), coord)
			print(self.pieces)


class Tic(_Piece):
	def canMove(coord):
		return False

	def __str__(self):
		return 'X'

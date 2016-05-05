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

import engine

class Game:
	def __init__(self):
		self.boards = {}

	def handle_json(self, obj):
		if obj['msgName'] == 'newGame':
			print('GameName:\t%s' % obj['rule'])

			# Create new board and add it to dictionary
			board_constructor = getattr(engine, obj['rule'])
			self.boards[0x1234] = board_constructor() # TODO: ID generator
		else:
			# Pass object to be handled by correct board
			self.boards[obj['id']].handle_json(obj)

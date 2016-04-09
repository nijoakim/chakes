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

import json

class Board:
	def __init__(self):
		self.pieces = {}
		self.jsons_to_send = []
		self.game_id = 0x1234 # TODO: Do this betterly

	def __str__(self):
		str_ = ''
		for piece in self.pieces.values():
			str_ += str(piece) +'\n'

		return str_

	def _send_json(self, json_obj):
		self.jsons_to_send.append(json.dumps(json_obj)) # TODO: Should jsons be dumped outside of this class?

	def _getPiece(self, dest):
		return self.pieces[dest] if dest in self.pieces else None

	def _createPiece(self, piece, dest):
		self.pieces[dest] = piece
		self._send_json({
			'msgName': 'updateAt',
			'dst':     dest,
			'piece':   3, # TODO: Only send essential info
		})

	def handle_json(self, obj):
		if obj['msgName'] == 'applyAction':
			self.action(
				obj['name'],
				(
					obj['src'][0], # x
					obj['src'][1], # y
				),
				(
					obj['dest'][0], # x
					obj['dest'][1], # y
				),
			)
		elif obj['msgName'] == 'newGame':
			print('GameName:\t%s' % obj['rule'])

			# board_constructor = getattr(engine, obj['rule'])
			# board            = board_constructor()
			obj['id']        = self.game_id

			self._send_json(obj)

	def action(self, src, dest):
		raise NotImplementedError('Implement please!')

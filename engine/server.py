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

import socket
import json

import engine

#============
# Game stuff
#============

board = engine.TicTacToe()

def handleJson(obj):
	if 'applyAction' in obj:
		board.action(
			obj['applyAction']['name'],
			(
				obj['applyAction']['src'][0],
				obj['applyAction']['src'][1],
			),
			(
				obj['applyAction']['dest'][0],
				obj['applyAction']['dest'][1],
			),
		)

#==============
# Server stuff
#==============

TCP_IP      = ''
TCP_PORT    = 3000
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()

try:
	print('Connection address:', addr)
	json_str = ''
	while True:
		data = conn.recv(BUFFER_SIZE)
		# Close connection
		if not data: break

		json_str += data.decode('utf-8')

		# If received end of transmission block
		if data[-1] == 0x17:
			try:
				json_obj = json.loads(json_str[0 : -1])
				handleJson(json_obj)
			except Exception as e:
				print(e)
				continue

		# conn.send(data) # echo whatever comes in
finally:
	print("Closed!")
	conn.close()
	print(board)

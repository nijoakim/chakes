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

#=========
# Imports
#=========

import socket
import json

import engine

#============
# Game stuff
#============

board = engine.TicTacToe()
game = engine.Game()

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
	json_str_buf = ''

	while True:
		data = conn.recv(BUFFER_SIZE) # Get data
		if not data: break            # Close connection if no data

		json_str += data.decode('utf-8')

		# If received end of transmission block
		# TODO: Split doesn't cut off after trailing \x17
		json_strs_to_process = json_str.split('\x17')
		print(json_strs_to_process)
		json_strs_to_process[0] = json_str_buf + json_strs_to_process[0]
		if data[-1] == 0x17:
			json_str_buf = json_strs_to_process.pop()
		json_str = ''

		print(json_strs_to_process)

		for json_str_to_process in json_strs_to_process:
			try:
				# Receive jsons
				print('\033[31;1mRecieved: '+ json_str_to_process +'\033[0m')
				json_obj = json.loads(json_str_to_process)
				board.handle_json(json_obj)

				# Send jsons
				for json_to_send in board.jsons_to_send:
					json_to_send += '\x17'
					print('\033[32;1mSending: '+ json_to_send +'\033[0m')
					conn.sendall(json_to_send.encode('utf-8'))
					board.jsons_to_send = []

			except Exception as e:
				print('Caught exception:')
				print(e)
				continue
finally:
	print("Closed!")
	conn.close()
	print(board)

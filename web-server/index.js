/* Copyright 2016 Kim Albertsson
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

var net     = require('net');
var express = require('express');
var app     = express();
var http    = require('http').Server(app);
var io      = require('socket.io')(http);

// Express stuff
app.use(express.static('../web-client'));

// app.get('/', function (req, res) {
//   res.send('Hello World!');
// });

http.listen(3000, function () {
  console.log('Example app listening on port 3000!');
});

// Socket.io stuff
var players = {1: false, 2: false};
io.on('connection', function(socket){

	var player;

	if (!players[1]) {
		player = 1;
		players[player] = true;
	} else if (!players[2]) {
		player = 2;
		players[player] = true;
	} else {
		player = -1;
	}

	socket.emit('player', player);
	console.log('a user connected', player);

	socket.on('move', function(msg){
		console.log('Player ' + player + ' made a move', msg);
		io.emit('move', msg);
	});

	socket.on('disconnect', function(){
		players[player] = false;
		console.log('user disconnected', player);
	});
});

// var ADDR = '192.168.1.12';
// // var ADDR = '127.0.0.1';
// var PORT = 3002;

// var client = new net.Socket();
// client.connect(PORT, ADDR, function() {
// 	console.log('Connected');
// 	// client.write('Hello, server! Love, Client.');
// 	sendObject(client, {test: "this is a long string!", a: 2, b: 3, c: 4});
// 	// sendObject(client, 123);
// });

// client.on('data', function(data) {
// 	console.log('Received: ' + data);
// 	client.destroy(); // kill client after server's response
// });

// client.on('close', function() {
// 	console.log('Connection closed');
// });


// function sendObject(socket, obj) {
// 	var json,
// 		ETB;

// 	ETB = '\x17';

// 	json = JSON.stringify(obj);

// 	socket.write(json + ETB);
// }
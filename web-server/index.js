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

/**
 * Start with
 * 	node index.js --engine-port 3000 --engine-addr 127.0.0.1
 */

var net     = require('net');
var express = require('express');
var app     = express();
var http    = require('http').Server(app);
var io      = require('socket.io')(http);

var argv    = require('minimist')(process.argv.slice(2));

var Engine  = require('./engine.js');

// Express stuff
// 
app.get('/game/:id', function (req, res, next) {
	console.log(req.params);
 	next();
});

// Serve static content last!
app.use('/game/:id', express.static('../web-client'));

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
	
	console.log('=== creating game ===');
	var id   = test1;
	var rule = 'TicTacToe';
	engine.sendMessage('newGame', id, rule);

	socket.on('move', function(msg){
		console.log('Player ' + player + ' made a move', msg);
		io.emit('move', msg);
	});

	socket.on('disconnect', function(){
		players[player] = false;
		console.log('user disconnected', player);
	});
});

// Engine
var engine_addr = argv['engine-addr'];
var engine_port = argv['engine-port'];
console.log('Connecting to Engine');
console.log('\tAddr - ' + engine_addr);
console.log('\tPort - ' + engine_port);

var engine = new Engine(engine_addr, engine_port);
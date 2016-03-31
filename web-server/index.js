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
app.use('/', express.static('../web-client'));

http.listen(3000, function () {
  console.log('Example app listening on port 3000!');
});

// Socket.io stuff
// TODO: A games object keeps track of id, players...
// {
// 	public-id : 'test1'    // used for communication between players and webserver
// 	private-id: 'hash-val' // used for communication w/ engine
// 	players   : [...]      // sockets for the other players of this game
// }
var games   = {};
var currentGlobalGame = {
	public_id : '',
	private_id: '',
	players   : [],
}
var nsp = io.of('/game/test1/');
nsp.on('connection', function(socket){

	currentGlobalGame.players.push(socket);
	var player = currentGlobalGame.players.length;

	socket.emit('player', player);
	console.log('a user connected', player);
	
	// console.log('=== creating game ===');
	// var id   = 'test1';
	// var rule = 'TicTacToe';
	// engine.sendMessage('newGame', id, rule);

	socket.on('webclient-newGame', function(msg){
		console.log('Player ' + player + ' requested new game', msg);
		engine.sendNewGameMessage(msg.rule);
		// TODO: Players of this room is now waiting for a new game of type x from engine
	});
	socket.on('webclient-move', function(msg){
		console.log('Player ' + player + ' made a move', msg);
		engine.sendMoveMessage('test1', msg.player, msg.src, msg.dst);
	});

	socket.on('engine-move', function (msg) {
		console.log('=== move message from engine ===')
		nsp.emit('webserver-move', msg);
	});

	socket.on('engine-newGame', function (msg) {
		console.log('=== new game from engine ===', msg.id, msg);
		currentGlobalGame.private_id = msg.id;
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
'use strict'

var net = require('net');
var chakesMessages = require('./messages.js');

module.exports = (function () {
	function Engine(addr, port) {
		var self = this;

		this.isConnected = false;
		this.socket      = new net.Socket();

		this.socket.connect(port, addr, function() {
			console.log('Connected to engine at (%s:%i)', addr, port);
			self.isConnected = true;
			// self.sendJSON({msgName:'newGame', id:'test1', rule:'TicTacToe'});
			// self.sendJSON({msgName:'applyAction',  name:'move', src:[0, 0], dest: [1, 1], id:'test1'});
		});

		/*
		 	Provide callback for when data is recevied from the engine.
		 */
		this.socket.on('data', function(data) {
			var jsons;

			var str  = '' + data;
			var data = str.split('\x17').slice(0,-1);

			jsons = data.map(JSON.parse);
			
			console.log('Received from engine: ');
			console.log(jsons);

			// idioticCounter++;
			// self.sendJSON({msgName:'applyAction',  name:'move', src:[0, 0], dest: [idioticCounter, 1], id:'test1'});

			// self.socket.destroy(); // kill client after server's response
		});

		this.socket.on('close', function() {
			console.log('Connection closed');
		});
	}

	Engine.prototype.sendNewGameMessage = function () {
		var message = chakesMessages.from.webserver.to.engine.newGame(rule);
		this.sendJSON(message);
	}

	Engine.prototype.sendMoveMessage = function (id, player, src, dst) {
		var message = chakesMessages.from.webserver.to.engine.applyAction(id, 'move', player, src, dst);
		this.sendJSON(message);
	}

	Engine.prototype.sendJSON = function (obj) {
		var json,
			ETB;

		ETB = '\x17';

		json = JSON.stringify(obj);

		console.log('Sending to Engine');
		console.log(obj);

		this.socket.write(json + ETB);
	}

	return Engine;
})();
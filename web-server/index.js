

var net = require('net');

var ADDR = '192.168.0.102';
var PORT = 8080; 

var client = new net.Socket();
client.connect(PORT, ADDR, function() {
	console.log('Connected');
	client.write('Hello, server! Love, Client.');
});

client.on('data', function(data) {
	console.log('Received: ' + data);
	client.destroy(); // kill client after server's response
});

client.on('close', function() {
	console.log('Connection closed');
});
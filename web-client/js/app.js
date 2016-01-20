var socket = io();

var player = 0;
// on checkboxchange, update player variable.

function sendTicTacToeMove (player, x, y) {
    var data;

    data = {player: player, x:x, y:y};
    socket.emit('move', data);
    console.log('Sent move to server', data);
}

grid = [0,0,0, 0,0,0, 0,0,0];

function move (player, x, y) {
    if ( x < 0 || x > 3 || y < 0 || y > 3) {
        console.error('Move out of bounds', {x:x, y:y});
        return -1;
    }

    if (player !== 1 && player !== 2) {
        console.error('Wrong player!', player);
        return -1;
    }

    pos = x  + 3*y;

    if (grid[pos] !== 0) {
        console.error('Square already occupied', {x:x, y:y});
        return -1;
    }

    // Preemptive rendering
    // board[x + 3*y] = player;
    
    // Commit to server
    sendTicTacToeMove(player, x, y);
}

socket.on('player', function (msg) {
    player = msg;
    document.title = "Player " + player;
});

var pieces = [];
socket.on('move', function (msg) {
    var piece,
        resource,
        x,
        y;

    console.log('Received server move message', msg);

    if (msg.player === 1) {
        resource = global_resources.white_pawn;
    } else if (msg.player === 2) {
        resource = global_resources.black_pawn;
    } else {
        console.error('Got incorrect player from server', msg.player);
        return -1;
    }

    piece = new PIXI.Sprite(resource.texture);

    x = msg.x * 100 + 50;
    y = msg.y * 100 + 50;

    piece.position.x = x;
    piece.position.y = y;

    piece.scale.x = 1;
    piece.scale.y = 1;

    piece.anchor.x = 0.5;
    piece.anchor.y = 0.5;

    board.addChildAt(piece, 0);
    pieces.push(piece);
});

// You can use either `new PIXI.WebGLRenderer`, `new PIXI.CanvasRenderer`, or `PIXI.autoDetectRenderer`
// which will try to choose the best renderer for the environment you are in.
var renderer = new PIXI.WebGLRenderer(400, 300);
renderer.backgroundColor = 0x66FF99;

// The renderer will create a canvas element for you that you can then insert into the DOM.
document.body.appendChild(renderer.view);

// You need to create a root container that will hold the scene you want to draw.
var stage = new PIXI.Container();

var black_pawn,
    white_pawn,
    global_resources;

// load the texture we need
PIXI.loader
.add('black_pawn', '/resources/pawn/black_pawn.png')
.add('white_pawn', '/resources/pawn/white_pawn.png')
.load(function (loader, resources) {
    global_resources = resources;
    animate();    
});

function animate() {
    // start the timer for the next animation loop
    requestAnimationFrame(animate);

    for (var i = pieces.length - 1; i >= 0; i--) {
        pieces[i].rotation += 0.01;
    };

    // this is the main render call that makes pixi draw your container and its children.
    renderer.render(stage);
}


// render board...
var board = new PIXI.Graphics();

board.beginFill(0xeeeeee);
board.lineStyle(5, 0xFF0000);
board.drawRect(0  , 0  , 100, 100);
board.drawRect(100, 100, 100, 100);
board.drawRect(200, 200, 100, 100);
board.drawRect(200, 0  , 100, 100);
board.drawRect(0  , 200, 100, 100);
board.endFill();

board.beginFill(0x22ee22);
board.drawRect(100, 0  , 100, 100);
board.drawRect(0  , 100, 100, 100);
board.drawRect(200, 100, 100, 100);
board.drawRect(100, 200, 100, 100);
board.endFill();

stage.addChild(board);
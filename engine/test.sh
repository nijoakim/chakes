#!/bin/bash

echo -ne '{"msgName": "newGame", "rule": "TicTacToe"}\x17' | telnet localhost 3000

#echo -ne '{"msgName": "newGame", "rule": "TicTacToe"}\x17{"msgName": "applyAction", "name": "move", "src": [0, 0], "dest": [4, 6]}\x17{"msgName": "applyAction", "name": "move", "src": [0, 0], "dest": [5, 6]}\x17' | telnet localhost 3000

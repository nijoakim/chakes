import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chakes.backend.models import MoveRequest
from chakes.backend.services import ChakesService, ConnectionManager, GameRoomService

router = APIRouter(prefix="/api")

rooms = GameRoomService()
connections = ConnectionManager()
chakes = ChakesService(rooms, connections)


@router.get("/rooms")
def rooms_list():
    return {"rooms": rooms.list()}


@router.post("/rooms")
def room_create():
    # TODO: Add name, starting pieces, player color...
    return {"room": rooms.create()}


@router.get("/rooms/{id}")
def room_state(id: uuid.UUID):
    return {"state": rooms[id].state}


@router.post("/rooms/{id}/move")
async def room_move(id: uuid.UUID, move: MoveRequest):
    await chakes.move(id, move)


@router.websocket("/rooms/{id}/ws")
async def game_state_ws(id: uuid.UUID, ws: WebSocket):
    await chakes.connect(id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        chakes.disconnect(id, ws)

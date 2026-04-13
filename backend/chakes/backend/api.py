from fastapi import APIRouter

from chakes.backend.services import ChakesService, GameRoomService

router = APIRouter(prefix="/api")

games = GameRoomService()
chakes = ChakesService()


@router.get("/games")
def games_list():
    return {"games": games.list()}


@router.post("/games")
def games_create():
    return {"game": games.create()}

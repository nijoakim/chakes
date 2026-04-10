from fastapi import APIRouter

from chakes.backend.services import ChakesService

router = APIRouter(prefix="/api")
service = ChakesService()


@router.get("/hello")
def hello():
    return {"message": service.hello()}

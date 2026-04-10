from fastapi import FastAPI

from chakes.backend.api import router

app = FastAPI()
app.include_router(router)

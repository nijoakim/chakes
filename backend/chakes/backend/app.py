from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chakes.backend.api import router

app = FastAPI()
app.include_router(router)

# Serve frontend static files (built by Vite) if the directory exists.
_static_dir = Path(__file__).resolve().parent.parent.parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")

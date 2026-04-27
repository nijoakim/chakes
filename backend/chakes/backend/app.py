from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from chakes.backend.api import router

app = FastAPI()
app.include_router(router)

# Serve frontend static files (built by Vite) if the directory exists.
_static_dir = Path(__file__).resolve().parent.parent.parent.parent / "static"
if _static_dir.is_dir():
    _index_html = _static_dir / "index.html"

    # Serve static assets (js, css, images, etc.)
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    # SPA fallback: serve index.html for any non-API route
    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        # Serve the actual file if it exists (e.g. favicon.ico)
        file = _static_dir / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(_index_html)

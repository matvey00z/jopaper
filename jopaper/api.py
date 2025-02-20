from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import logging
import uuid
from jopaper import Generators
from jopaper import tracing
from typing import Annotated, Optional


class Settings(BaseSettings):
    base_url: str = "localhost"
    screen_w_default: int = 1920
    screen_h_default: int = 1080


settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

generators = Generators(logger)

app = FastAPI(on_shutdown=[generators.stop])


@app.get("/wallpaper")
async def wallpaper(
    session_id: Optional[str] = None,
    screen_w: Annotated[
        int, Query(title="Screen width", ge=100, le=8000)
    ] = settings.screen_w_default,
    screen_h: Annotated[
        int, Query(title="Screen height", ge=100, le=8000)
    ] = settings.screen_h_default,
    r: Optional[str] = None,  # to make urls unique; ignore
):
    generator = await generators.get_generator(screen_w, screen_h)
    filename = await generator.aget_next_wallpaper(session_id)
    return FileResponse(filename, filename="wallpaper.png")


# JSON endpoint for RandomWallpaperGnome3 extension
class RWG3Response(BaseModel):
    url: str


@app.get("/rwg3")
async def rwg3() -> RWG3Response:
    return RWG3Response(url="/".join([settings.base_url, "wallpaper"]))


@app.get("/")
async def index(session_id: Optional[str] = None) -> HTMLResponse:
    if session_id is None or len(session_id) != 32:
        session_id = uuid.uuid4().hex
        return RedirectResponse(f"/?session_id={session_id}")
    else:
        session_id = session_id[:32]
    with open("jopaper/static/index.html") as f:
        page = f.read()
        page = page.replace("SESSION_ID", session_id)
        return HTMLResponse(content=page, status_code=200)


tracing.setup_tracer(app, generators)

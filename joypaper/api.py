from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import logging
from joypaper import Generators


class Settings(BaseSettings):
    base_url: str = "localhost"
    data_dir: str = "/tmp/joypaper-data"
    screen_w_default: int = 3440
    screen_h_default: int = 1440


settings = Settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

generators = Generators(logger)

app = FastAPI(on_shutdown=[generators.stop])


@app.get("/wallpaper")
async def wallpaper(
    screen_w: int = settings.screen_w_default, screen_h: int = settings.screen_h_default
):
    generator = await generators.get_generator(screen_w, screen_h)
    filename = await generator.aget_next_wallpaper()
    return FileResponse(filename, filename="wallpaper.png")


# JSON endpoint for RandomWallpaperGnome3 extension
class RWG3Response(BaseModel):
    url: str


@app.get("/rwg3")
async def rwg3() -> RWG3Response:
    return RWG3Response(url="/".join([settings.base_url, "wallpaper"]))


@app.get("/")
async def index() -> HTMLResponse:
    with open("joypaper/static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

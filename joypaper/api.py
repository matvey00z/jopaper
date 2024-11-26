from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import logging
import os
from joypaper import Generator


class Settings(BaseSettings):
    base_url: str = "localhost"
    data_dir: str = "/tmp/joypaper-data"


settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

generator = Generator(
    download_dir=os.path.join(settings.data_dir, "/tmp/downloads"),
    used_dir=os.path.join(settings.data_dir, "/tmp/downloads/used"),
    wallpaper_dir=os.path.join(settings.data_dir, "/tmp/wallpapers"),
    screen_w=3440,
    screen_h=1440,
    logger=logger,
)

app = FastAPI()


@app.get("/wallpaper")
async def wallpaper():
    filename = generator.get_next_wallpaper()
    return FileResponse(filename, filename="wallpaper.png")


# JSON endpoint for RandomWallpaperGnome3 extension
class RWG3Response(BaseModel):
    url: str


@app.get("/rwg3")
async def rwg3() -> RWG3Response:
    return RWG3Response(url="/".join([settings.base_url, "wallpaper"]))

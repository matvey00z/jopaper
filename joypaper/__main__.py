import random
import logging

from joypaper.generator import Generator

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


generator = Generator(
    download_dir="downloads",
    used_dir="downloads/used",
    wallpaper_dir="wallpapers",
    screen_w=3440,
    screen_h=1440,
    logger=logger,
)


if __name__ == "__main__":
    random.seed()

    wallpaper_filename = generator.get_next_wallpaper()
    logging.info(f"Wallpaper saved to: {wallpaper_filename}")

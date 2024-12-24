from joypaper import Generator
import os
import logging


def test_e2e(tmp_path):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    download_dir = os.path.join(tmp_path, "downloads")
    used_dir = os.path.join(tmp_path, "used")
    wallpaper_dir = os.path.join(tmp_path, "wallpapers")
    generator = Generator(
        download_dir=download_dir,
        used_dir=used_dir,
        wallpaper_dir=wallpaper_dir,
        screen_w=3440,
        screen_h=1440,
        logger=logger,
        is_async=False,
    )

    wallpaper_filename = generator.get_next_wallpaper()

    assert os.path.isdir(download_dir)
    assert os.path.isdir(used_dir)
    assert os.path.isdir(wallpaper_dir)

    assert os.path.isfile(wallpaper_filename)
    assert os.stat(wallpaper_filename).st_size > 0

    used_imgs = list(os.listdir(used_dir))
    assert used_imgs
    for fname in used_imgs:
        fullname = os.path.join(used_dir, fname)
        assert os.path.isfile(fullname)
        assert os.stat(fullname).st_size > 0

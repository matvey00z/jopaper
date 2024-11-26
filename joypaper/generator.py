from joypaper import reactor
from joypaper.storage import Storage
from joypaper.layout import SubImage, Wall
from PIL import Image
import random
from typing import List


class Generator:
    def __init__(
        self,
        download_dir: str,
        used_dir: str,
        wallpaper_dir: str,
        screen_w: int,
        screen_h: int,
        logger,
    ):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.logger = logger
        filters = reactor.get_default_filters(screen_w, screen_h)
        self.source = reactor.Source(logger, filters)
        self.storage = Storage(download_dir, used_dir, wallpaper_dir)
        self.feed = self._wallpaper_feed()

    def get_next_wallpaper(self) -> str:
        return next(self.feed)

    def _download_random_image(self):
        image = self.source.get_image()
        try:
            self.logger.debug(f"Downloading image {image.url}")
            fname = self.storage.download_file(image.url, image.file_type)
        except Exception:
            self.logger.error(f"Error downloading {image.url}", exc_info=True)
            return None
        self.logger.info(f"Image {image.url} successfully saved to {fname}")
        return fname

    def _random_file_feed(self):
        filenames = self.storage.get_downloads()
        for f in filenames:
            yield f
        while True:
            filename = self._download_random_image()
            if filename:
                yield filename

    def _gen_random_wall(self, images: List[SubImage]):
        random.shuffle(images)
        wall = Wall(self.screen_w, self.screen_h)
        layout = []
        ratio1 = self.screen_w / self.screen_h
        ratio4 = self.screen_w / 4 / self.screen_h
        layout_matched = False

        for image in images:
            ratio = image.get_ratio()
            f1 = abs(ratio - ratio1)
            f4 = abs(ratio - ratio4)
            if f1 < f4:
                # Go for single picture
                image.to_box(0, 0, self.screen_w, self.screen_h)
                layout = [image]
                layout_matched = True
                break
            else:
                # Go for 4 in row
                image.to_box(0, 0, self.screen_w / 4, self.screen_h)
                layout.append(image)
                if len(layout) == 4:
                    layout_matched = True
                    break
        if not layout_matched:
            return None
        for image in layout:
            wall.add(image)
        return wall

    def _wallpaper_feed(self):
        images = {}
        for filename in self._random_file_feed():
            p = self._parse_image(filename)
            if p is None:
                continue
            images[filename] = p
            wall = self._gen_random_wall(list(images.values()))
            if wall is None:
                continue
            used_files, image = wall.get_png()
            wallpaper_filename = self.storage.save_wallpaper(image)
            for f in used_files:
                del images[f]
                self.storage.mark_used(f)
            yield wallpaper_filename

    def _parse_image(self, f):
        try:
            with Image.open(f) as img:
                w, h = img.size
        except Exception:
            self.logger.error(f"Can't parse an image: {f}", exc_info=True)
            return None
        return SubImage(f, w, h)

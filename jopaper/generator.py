from jopaper import reactor
from jopaper.storage import Storage
from jopaper.layout import SubImage, Wall
from PIL import Image
import random
from typing import List
import asyncio
import functools


class LogTracer:
    def __init__(self, logger):
        self.logger = logger

    def start_as_current_span(self, name):
        class Span:
            def __init__(self, name, logger):
                self.name = name
                self.logger = logger

            def __enter__(self):
                self.logger.debug(f"trace: enter {self.name}")
                return self

            def __exit__(self, *args, **kwargs):
                self.logger.debug(f"trace: exit {self.name}")
                pass

            def __call__(self, f, *args, **kwargs):
                @functools.wraps(f)
                def w(*args, **kwargs):
                    with self:
                        return f(*args, **kwargs)

                return w

        return Span(name, self.logger)


class Generator:
    def __init__(
        self,
        download_dir: str,
        used_dir: str,
        wallpaper_dir: str,
        screen_w: int,
        screen_h: int,
        logger,
        max_images: int = None,
        is_async: bool = False,
        tracer=None,
    ):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.logger = logger
        filters = reactor.get_default_filters(screen_w, screen_h)
        self.source = reactor.Source(logger, filters)
        self.storage = Storage(download_dir, used_dir, wallpaper_dir, logger)
        self.is_async = is_async
        self.tracer = tracer if tracer is not None else LogTracer(self.logger)
        self.feed = self._wallpaper_feed()
        if self.is_async:
            self.wallpapers_queue = asyncio.Queue(maxsize=max_images)
        self.logger.debug(f"Created new generator: {vars(self)}")

    async def start(self):
        assert self.is_async
        self.logger.debug(f"Starting generator {self.screen_w}x{self.screen_h}")
        try:
            async for wallpaper in self.feed:
                self.logger.debug(f"Saving wallpaper [{wallpaper}] to queue")
                await self.wallpapers_queue.put(wallpaper)
        except asyncio.QueueShutDown:
            pass

    async def stop(self):
        assert self.is_async
        self.wallpapers_queue.shutdown(immediate=True)

    def get_next_wallpaper(self) -> str:
        assert not self.is_async
        return asyncio.run(anext(self.feed))

    async def aget_next_wallpaper(self) -> str:
        assert self.is_async
        wallpaper = await self.wallpapers_queue.get()
        self.wallpapers_queue.task_done()
        return wallpaper

    async def _run_bg(self, f):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, f)

    async def _download_random_image(self):
        @self.tracer.start_as_current_span("download_random_image")
        def f():
            image = self.source.get_image()
            try:
                fname = self.storage.download_file(image.url, image.file_type)
            except Exception as e:
                self.logger.error(f"Error downloading {image.url}: [{e}]")
                return None
            self.logger.info(f"Image {image.url} successfully saved to {fname}")
            return fname

        return await self._run_bg(f)

    async def _random_file_feed(self):
        filenames = self.storage.get_downloads()
        for f in filenames:
            yield f
        while True:
            filename = await self._download_random_image()
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

    async def _wallpaper_feed(self):
        images = {}
        async for filename in self._random_file_feed():

            @self.tracer.start_as_current_span("generate_wallpaper")
            def f():
                with self.tracer.start_as_current_span("parse_image"):
                    p = self._parse_image(filename)
                if p is None:
                    return None
                images[filename] = p
                with self.tracer.start_as_current_span("generate_layout"):
                    wall = self._gen_random_wall(list(images.values()))
                if wall is None:
                    return None
                used_files, image = wall.get_png(tracer=self.tracer)
                with self.tracer.start_as_current_span("save_wallpaper"):
                    wallpaper_filename = self.storage.save_wallpaper(image)
                for f in used_files:
                    del images[f]
                    self.storage.mark_used(f)
                return wallpaper_filename

            wallpaper_filename = await self._run_bg(f)
            if wallpaper_filename:
                yield wallpaper_filename

    def _parse_image(self, f):
        try:
            with Image.open(f) as img:
                w, h = img.size
        except Exception:
            self.logger.error(f"Can't parse an image: {f}", exc_info=True)
            return None
        return SubImage(f, w, h)

from pydantic_settings import BaseSettings
import asyncio
from jopaper import Generator
import os


class Settings(BaseSettings):
    max_generators: int = 10
    max_images_per_generator: int = 10
    fs_root: str = "/tmp/jopaper/generator"


settings = Settings()


class Generators:
    def __init__(self, logger):
        self.logger = logger

        self.lock = asyncio.Lock()
        self.generators = {}
        self.usage = {}

        self.max_generators = settings.max_generators
        self.max_usage = 10 * settings.max_generators

        self.tasks = {}

    async def get_generator(self, screen_w: int, screen_h: int):
        key = (screen_w, screen_h)
        async with self.lock:
            self.usage[key] = self.usage.get(key, 0) + 1
            if key in self.generators:
                return self.generators[key]
            if len(self.generators) >= self.max_generators:
                gens = _sort_k_by_v_join(self.generators, self.usage)
                gen_to_remove = gens[: -self.max_generators]
                for gen in gen_to_remove:
                    self._remove_generator(gen)
            if len(self.usage) > self.max_usage:
                usage_to_remove = _sort_k_by_v(self.usage)[: -self.max_usage]
                for u in usage_to_remove:
                    del self.usage[u]
            new_gen = await self._new_generator(screen_w, screen_h)
            self.tasks[key] = asyncio.create_task(new_gen.start())
            self.generators[key] = new_gen
        return new_gen

    async def stop(self):
        self.logger.debug("Stopping generators")
        for key in list(self.generators.keys()):
            self._remove_generator(key)
        self.process_pool.shutdown()

    async def _new_generator(self, screen_w, screen_h):
        new_gen = Generator(
            download_dir=os.path.join(
                settings.fs_root, "download", f"{screen_w}x{screen_h}"
            ),
            used_dir=os.path.join(settings.fs_root, "used", f"{screen_w}x{screen_h}"),
            wallpaper_dir=os.path.join(
                settings.fs_root, "wallpaper", f"{screen_w}x{screen_h}"
            ),
            screen_w=screen_w,
            screen_h=screen_h,
            max_images=settings.max_images_per_generator,
            logger=self.logger,
            is_async=True,
        )
        return new_gen

    async def _remove_generator(self, key):
        self.logger.debug(f"Removing generator [{key}]")
        # TODO: check that task is cancelled
        self.generators[key].stop()
        del self.generators[key]
        del self.tasks[key]


def _sort_k_by_v(d: dict):
    """
    Return keys of the dict sorted by their values
    """
    return sorted((k for k, v in d.items()), key=lambda kv: kv[1])


def _sort_k_by_v_join(left: dict, right: dict, default=0):
    """
    Return keys of left dict sorted by their values in right dict
    """
    return sorted((k for k, v in left), key=lambda kv: right[kv[0]])

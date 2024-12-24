import os
import requests
from typing import List
import shutil
import datetime
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    max_used_cnt: int = 20
    max_wallpaper_cnt: int = 20


settings = Settings()

_request_timeout = 1.0


class Storage:
    def __init__(self, download_dir: str, used_dir: str, wallpaper_dir: str, logger):
        self.logger = logger
        self.download_dir = download_dir
        self.used_dir = used_dir
        self.wallpaper_dir = wallpaper_dir

        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(used_dir, exist_ok=True)
        os.makedirs(wallpaper_dir, exist_ok=True)

        self.downloads = set(_read_directory(self.download_dir, "img"))

        self.counter = 0

    def download_file(self, url: str, ftype: str) -> str:
        path = _get_path(self.download_dir, "img", self._count(), ftype)
        response = requests.get(url, timeout=_request_timeout)
        if response.status_code not in [200, 302]:
            raise RuntimeError("Unexpected response {}".format(response.status_code))
        with open(path, "wb") as f:
            f.write(response.content)

        self.downloads.add(path)
        return path

    def get_downloads(self) -> List[str]:
        return list(self.downloads)

    def mark_used(self, src) -> str:
        self.downloads.remove(src)
        ftype = src.split(".")[-1]
        dest = _get_path(self.used_dir, "img", self._count(), ftype)
        shutil.move(src, dest)

        old_files = _clean_directory(self.used_dir, "img", settings.max_used_cnt)
        if old_files:
            self.logger.debug(
                f"Used images clean up: removed {len(old_files)} old files"
            )
        return dest

    def save_wallpaper(self, image: bytes) -> str:
        ftype = "png"
        fname = _get_path(self.wallpaper_dir, "wallpaper", self._count(), ftype)
        with open(fname, "wb") as f:
            f.write(image)

        old_files = _clean_directory(
            self.wallpaper_dir, "wallpaper", settings.max_wallpaper_cnt
        )
        if old_files:
            self.logger.debug(
                f"Wallpapers clean up: removed {len(old_files)} old files"
            )
        return fname

    def _count(self):
        self.counter += 1
        return self.counter


def _read_directory(dirname, prefix):
    for fname in os.listdir(dirname):
        fullname = os.path.join(dirname, fname)
        if not os.path.isfile(fullname):
            continue
        if not fname.startswith(prefix):
            continue
        yield fullname


def _get_path(dirname, prefix, count, ftype):
    now = datetime.datetime.now().isoformat("_", "milliseconds")
    return os.path.join(dirname, f"{prefix}-{now}-{count}.{ftype}")


def _clean_directory(dirname, prefix, to_keep):
    files = _read_directory(dirname, prefix)
    files = sorted(files)
    files = files[:-to_keep]
    for file in files:
        Path.unlink(file, missing_ok=True)
    return files

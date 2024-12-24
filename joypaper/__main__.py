import logging
import argparse
import os
import tempfile

from joypaper.generator import Generator


class DirManager:
    def __init__(self, dirname=None):
        self.dirname = dirname
        self.tempdir = None

    def __enter__(self):
        if self.dirname is None:
            self.tempdir = tempfile.TemporaryDirectory()
            return self.tempdir.name
        return self.dirname

    def __exit__(self, *args, **kwargs):
        if self.tempdir is not None:
            self.tempdir.cleanup


def main():
    parser = argparse.ArgumentParser(
        description="Joypaper: Generate random wallpapers from joyreactor.cc's posts."
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--dir", type=str, default=None, help="Directory for persistent storage."
    )

    parser.add_argument(
        "-W",
        "--width",
        type=int,
        default=1920,
        help="Set the screen width. Default is 1920.",
    )

    parser.add_argument(
        "-H",
        "--height",
        type=int,
        default=1080,
        help="Set the screen height. Default is 1080.",
    )

    parser.add_argument(
        "-p",
        "--path",
        type=str,
        default="wallpaper.png",
        help='The path where the wallpaper will be saved. Default is "wallpaper.png"',
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARN)
    logger = logging.getLogger(__name__)

    with DirManager(args.dir) as dir:
        generator = Generator(
            download_dir=dir,
            used_dir=os.path.join(dir, "used"),
            wallpaper_dir=os.path.join(dir, "wallpapers"),
            screen_w=args.width,
            screen_h=args.height,
            logger=logger,
        )
        wallpaper_filename = generator.get_next_wallpaper()
        # Write file content manually to support both file and pipe outputs
        with open(args.path, "wb") as o:
            with open(wallpaper_filename, "rb") as i:
                o.write(i.read())

    logging.info(f"Wallpaper saved to: {args.path}")


if __name__ == "__main__":
    main()

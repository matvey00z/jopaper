# JoyPaper

JoyPaper generates random wallpapers by combining images published on https://joyreactor.cc

This project is NOT affiliated or in any way associated with JoyReactor.

## Usage

### Standalone utility

```bash
# Generate wallpaper.png in current directory using docker:
sudo docker compose run --build cli

# Generate wallpaper.png in current directory using poetry:
poetry run python -m joypaper

# See possible options:
poetry run python -m joypaper -h
```

### Server

```bash
# With docker:
sudo docker compose up --build

# With poetry:
poetry run fastapi run joypaper/api.py
```

Download random wallpaper: http://127.0.0.1:8000/wallpaper

Set custom screen size: http://127.0.0.1:8000/wallpaper?screen_w=1920&screen_h=1080

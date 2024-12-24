# JoPaper

JoPaper generates random wallpapers by combining images published on https://joyreactor.cc

This project is NOT affiliated or in any way associated with JoyReactor.

## Usage

### Standalone utility

```bash
# Generate wallpaper.png in current directory using docker:
sudo docker compose run --build cli

# Generate wallpaper.png in current directory using poetry:
poetry run python -m jopaper

# See possible options:
poetry run python -m jopaper -h
```

### Server

```bash
# With docker:
sudo docker compose up --build

# With poetry:
poetry run fastapi run jopaper/api.py
```

Then go to http://127.0.0.1:8000/

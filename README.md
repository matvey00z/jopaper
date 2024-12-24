# JoyPaper

JoyPaper generates random wallpapers by combining images published on https://joyreactor.cc

This project is NOT affiliated or in any way associated with JoyReactor.

## Usage

### Standalone utility

Generate wallpaper.png in current directory:

```bash
poetry run python -m joypaper
```

For details see:
```bash
poetry run python -m joypaper -h
```

### Server

Start server:
```bash
poetry run fastapi run joypaper/api.py
```

Then go to http://127.0.0.1:8000/wallpaper

# asciify

[![PyPI](https://img.shields.io/pypi/v/asciifyy)](https://pypi.org/project/asciifyy/)
[![Python](https://img.shields.io/pypi/pyversions/asciifyy)](https://pypi.org/project/asciifyy/)
[![CI](https://github.com/markmysler/asciify/actions/workflows/ci.yml/badge.svg)](https://github.com/markmysler/asciify/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/markmysler/asciify/blob/main/LICENSE)

Turn any image into ASCII art or colored block art, right in your terminal.

| Original | `asciify -w 80` | `asciify -w 80 -m blocks` |
|---|---|---|
| ![Original image: a sunset over mountains](https://raw.githubusercontent.com/markmysler/asciify/main/docs/example-original.png) | ![The same image as colored ASCII art](https://raw.githubusercontent.com/markmysler/asciify/main/docs/example-ascii.png) | ![The same image as colored half blocks](https://raw.githubusercontent.com/markmysler/asciify/main/docs/example-blocks.png) |

## Features

- **Two styles:** characters picked by brightness (`ascii`), or half-block cells with two colored pixels each (`blocks`), for twice the vertical detail.
- **24-bit color**, written compactly. Output is plain text when you pipe or redirect it, and respects [`NO_COLOR`](https://no-color.org).
- **Fits your terminal** by default, in width and height.
- **Plays animated GIFs and WebPs** in the terminal.
- **Reads files, URLs or standard input:** PNG, JPEG, GIF, WebP, BMP, TIFF and everything else [Pillow](https://python-pillow.org) can open.
- **Saves** to text or to a standalone HTML page.
- **Light terminals:** `--invert` swaps the brightness mapping.
- **Custom character ramps** with `--chars`.
- **Transparency:** transparent pixels stay blank.

## Install

**With pip** (any OS, Python 3.9+):

```bash
pip install asciifyy
```

The package is called `asciifyy` (two y's) because `asciify` was already taken on PyPI. The command it installs is `asciify`.

**With apt** (Debian 12+, Ubuntu 22.04+):

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://markmysler.github.io/asciify/asciify-archive-keyring.gpg | sudo tee /etc/apt/keyrings/asciify.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/asciify.gpg] https://markmysler.github.io/asciify stable main" | sudo tee /etc/apt/sources.list.d/asciify.list
sudo apt-get update
sudo apt-get install asciifyy
```

`apt-get upgrade` then picks up new releases. Each [GitHub Release](https://github.com/markmysler/asciify/releases) also has the `.deb` attached, which you can install directly with `sudo apt install ./asciifyy_<version>_all.deb`.

## Usage

```bash
asciify photo.jpg                          # fit the terminal, in color
asciify photo.jpg -m blocks                # colored half blocks
asciify photo.jpg -w 60 -nc                # 60 columns, no color
asciify logo.png --invert                  # for a light terminal background
asciify dance.gif --animate --loop 3       # play an animated GIF three times
asciify https://example.com/cat.png        # straight from a URL
curl -s https://example.com/cat.png | asciify -
asciify photo.jpg -o photo.html            # save a web page
asciify photo.jpg -o photo.txt -w 120      # save plain text
```

### Options

| Option | What it does |
|---|---|
| `-w`, `--width N` | Output width in characters. Default: fit the terminal (100 when not printing to one). |
| `-m`, `--mode ascii\|blocks` | Characters by brightness (default), or half-block cells. |
| `--color auto\|always\|never` | `auto` colors terminal output and HTML files, unless `NO_COLOR` is set. |
| `-nc`, `--no-color` | Same as `--color never`. |
| `-i`, `--invert` | Invert brightness, for light backgrounds. |
| `-c`, `--chars RAMP` | Characters for ascii mode, from least to most ink, e.g. `' .:-=+*#%@'`. |
| `-o`, `--output FILE` | Save instead of printing; `.html`/`.htm` saves a web page. |
| `-a`, `--animate` | Play an animated image in the terminal (Ctrl+C stops). |
| `--loop N` | With `--animate`, play N times (0, the default, loops forever). |
| `-V`, `--version` | Print the version. |

Exit status is 0 on success, 1 if the image can't be read or the output can't be written, and 2 for invalid options.

### From Python

```python
from PIL import Image
import asciify

print(asciify.image_to_ascii(Image.open("photo.jpg"), width=80))
print(asciify.image_to_ascii(Image.open("photo.jpg"), width=80, mode="blocks"))
print(asciify.image_to_ascii(Image.open("photo.jpg"), width=80, color=False, chars=" .oO@"))
```

`asciify.render(...)` returns the grid of cells (character, foreground, background) if you want to format it yourself. `asciify.to_ansi`, `to_text` and `to_html` are the formatters the command uses.

## How it works

1. **Size:** the image is scaled to the output width. The height is halved, because terminal cells are about twice as tall as they are wide. It shrinks further if needed to fit the terminal's height.
2. **ascii mode:** each pixel's perceived brightness (`0.299 R + 0.587 G + 0.114 B`) picks a character from a ramp that runs from little ink (` `) to a lot (`$`). In color, the character is drawn in the pixel's own color.
3. **blocks mode:** each cell covers two pixels stacked vertically. It's drawn as `▀`, with the top pixel as the foreground color and the bottom pixel as the background.
4. **Output:** a color escape is written only when the color changes, and every line ends with a reset. HTML output uses `<span>`s inside a `<pre>`.

Color output needs a terminal with 24-bit color. That covers Windows Terminal, iTerm2, GNOME Terminal, Konsole, kitty, WezTerm, Alacritty, VS Code and most modern terminals.

## Development

```bash
git clone https://github.com/markmysler/asciify.git
cd asciify
pip install -e ".[dev]"
pytest
ruff check .
mypy
```

Build the `.deb` locally (on Debian or Ubuntu) with `sh packaging/debian/build-deb.sh`.

**Releasing:**
1. Bump `__version__` in `src/asciify/__init__.py` and add a section to [CHANGELOG.md](CHANGELOG.md).
2. Publish a GitHub Release tagged with that version.

CI then publishes to PyPI, attaches the wheel, sdist and `.deb` to the release, and updates the apt repository.

## License

MIT. See [LICENSE](LICENSE).

## Author

Mark Mysler ([@markmysler](https://github.com/markmysler))

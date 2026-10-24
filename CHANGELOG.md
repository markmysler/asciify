# Changelog

## 1.1.0

### Added
- **Blocks mode** (`-m blocks`): half-block cells with 24-bit foreground and background colors, for twice the vertical detail.
- **Animated GIF and WebP playback** in the terminal (`--animate`, `--loop N`).
- **More inputs:** http(s) URLs, and `-` for standard input.
- **Saving** with `-o FILE`: plain text, ANSI text (`--color always`) or a standalone HTML page (`.html`).
- `--invert` for light terminal backgrounds, and `--chars` for a custom character ramp.
- `--color auto|always|never`. `auto` colors only real terminals and honours `NO_COLOR`.
- `--version`.
- An apt repository and a `.deb` on every GitHub Release (see the README).

### Changed
- By default the output fits the terminal (width and height); it's 100 columns wide when not printing to a terminal.
- Brightness uses perceived luminance instead of a plain RGB average.
- Monochrome output uses a 10-level ramp (`" .:-=+*#%@"`); the color ramp's stray duplicate backslash is gone.
- Color escapes are written only when the color changes, and each line ends with a reset. Output is several times smaller.
- Transparent pixels are left blank instead of turning black.
- Redirected output is plain text on every platform (it used to keep the escapes on Linux and macOS).
- `colorama` is only installed on Windows.
- Requires Python 3.9+ and Pillow 9–14.
- The code is a package (`asciify.render`, `asciify.output`, `asciify.loader`, `asciify.cli`), with a Python API: `asciify.image_to_ascii(image, width, ...)`.

### Fixed
- Pixels are read with `Image.tobytes()`. `Image.getdata()` was deprecated and is removed in Pillow 14.
- Very wide images (and `-w 0`, `-w -5`) no longer crash. Widths below 1 are rejected with a usage error.
- Errors (a missing file, a non-image, a directory) go to stderr and exit with status 1, as the man page says.
- Image files are closed after reading.

### Removed
- `setup.py`, `requirements.txt`, `asciify.bat`, and the stale copies of the script under `build/` and `usr/`.
- `convert_image_to_ascii` now raises `asciify.loader.AsciifyError` on a bad file instead of returning the error text.

## 1.0.4

- Separate character ramps for color and no-color output.

## 1.0.0

- First release: colored ASCII art with `-w/--width` and `-nc/--no-color`.

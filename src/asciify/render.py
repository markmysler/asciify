"""Turn an image into a grid of character cells.

A cell is a character plus an optional foreground and background color.
The grid knows nothing about terminals or files; see ``asciify.output`` for
turning it into ANSI text, plain text or HTML.
"""

from typing import List, Optional, Sequence, Tuple

from PIL import Image

RGB = Tuple[int, int, int]
Cell = Tuple[str, Optional[RGB], Optional[RGB]]
Grid = List[List[Cell]]

# Ramps are ordered from least ink to most ink. On a dark terminal a dark
# pixel gets the first character (little ink) and a bright pixel the last.
# --invert flips this for light backgrounds.
DETAILED_RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
SIMPLE_RAMP = " .:-=+*#%@"

MODES = ("ascii", "blocks")

# Terminal cells are about twice as tall as they are wide
CELL_ASPECT = 0.5

# Pixels less opaque than this are drawn as empty space
ALPHA_THRESHOLD = 128

_LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

_BLANK: Cell = (" ", None, None)


def luminance(r: int, g: int, b: int) -> int:
    """Perceived brightness, 0-255 (ITU-R BT.601 weights)."""
    return (299 * r + 587 * g + 114 * b) // 1000


def grid_size(image_size: Tuple[int, int], width: int, max_rows: Optional[int] = None) -> Tuple[int, int]:
    """Columns and rows of the grid for an image drawn ``width`` cells wide.

    The width shrinks if needed so the grid is at most ``max_rows`` tall.
    Both results are at least 1, however wide or tall the image.
    """
    if width < 1:
        raise ValueError("width must be at least 1")
    img_w, img_h = image_size
    ratio = img_h / img_w * CELL_ASPECT
    rows = max(1, int(width * ratio + 0.5))
    if max_rows is not None and rows > max_rows:
        width = max(1, int(max_rows / ratio))
        rows = max(1, min(max_rows, int(width * ratio + 0.5)))
    return width, rows


def prepare(image: Image.Image, columns: int, rows: int, mode: str) -> Image.Image:
    """Convert to RGBA and resize to one pixel per cell (two in blocks mode)."""
    if image.mode != "RGBA":
        try:
            image = image.convert("RGBA")
        except ValueError:  # modes such as I;16 have no direct RGBA conversion
            image = image.convert("RGB").convert("RGBA")
    pixel_rows = rows * 2 if mode == "blocks" else rows
    return image.resize((columns, pixel_rows), _LANCZOS)


def _pixels(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    data = image.tobytes()
    return [(data[i], data[i + 1], data[i + 2], data[i + 3]) for i in range(0, len(data), 4)]


def render_ascii(image: Image.Image, ramp: Sequence[str] = DETAILED_RAMP, color: bool = True,
                 invert: bool = False) -> Grid:
    """One character per pixel of an RGBA image, picked by brightness."""
    if len(ramp) < 2:
        raise ValueError("a character ramp needs at least 2 characters")
    width = image.width
    pixels = _pixels(image)
    last = len(ramp) - 1
    grid: Grid = []
    for y in range(image.height):
        row: List[Cell] = []
        for r, g, b, a in pixels[y * width:(y + 1) * width]:
            if a < ALPHA_THRESHOLD:
                row.append(_BLANK)
                continue
            level = luminance(r, g, b)
            if invert:
                level = 255 - level
            char = ramp[(level * last + 127) // 255]
            row.append((char, (r, g, b) if color else None, None))
        grid.append(row)
    return grid


def render_blocks(image: Image.Image, color: bool = True, invert: bool = False) -> Grid:
    """Two pixels per cell, stacked: the upper half block takes the top one.

    In color the top pixel is the foreground of "▀" and the bottom pixel its
    background, which doubles the vertical resolution. Without color each
    half is on or off by brightness, drawn with "▀", "▄", "█" or a space.
    """
    width = image.width
    pixels = _pixels(image)
    grid: Grid = []
    for y in range(0, image.height - 1, 2):
        top_row = pixels[y * width:(y + 1) * width]
        bottom_row = pixels[(y + 1) * width:(y + 2) * width]
        row: List[Cell] = []
        for (tr, tg, tb, ta), (br, bg, bb, ba) in zip(top_row, bottom_row):
            top_on = ta >= ALPHA_THRESHOLD
            bottom_on = ba >= ALPHA_THRESHOLD
            if color:
                top: RGB = (tr, tg, tb)
                bottom: RGB = (br, bg, bb)
                if top_on and bottom_on:
                    row.append(("▀", top, bottom))
                elif top_on:
                    row.append(("▀", top, None))
                elif bottom_on:
                    row.append(("▄", bottom, None))
                else:
                    row.append(_BLANK)
            else:
                top_on = top_on and _lit(tr, tg, tb, invert)
                bottom_on = bottom_on and _lit(br, bg, bb, invert)
                char = {(True, True): "█", (True, False): "▀", (False, True): "▄"}.get((top_on, bottom_on), " ")
                row.append((char, None, None))
        grid.append(row)
    return grid


def _lit(r: int, g: int, b: int, invert: bool) -> bool:
    return (luminance(r, g, b) >= 128) != invert


def render(image: Image.Image, width: int, mode: str = "ascii", color: bool = True, invert: bool = False,
           chars: Optional[str] = None, max_rows: Optional[int] = None) -> Grid:
    """Render a Pillow image as a grid ``width`` cells wide (or narrower, to fit ``max_rows``)."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}")
    columns, rows = grid_size(image.size, width, max_rows)
    prepared = prepare(image, columns, rows, mode)
    if mode == "blocks":
        return render_blocks(prepared, color, invert)
    ramp = chars if chars is not None else (DETAILED_RAMP if color else SIMPLE_RAMP)
    return render_ascii(prepared, ramp, color, invert)

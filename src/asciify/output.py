"""Turn a rendered grid into plain text, ANSI-colored text or HTML."""

import html
from itertools import groupby
from typing import List, Optional, Tuple

from asciify.render import RGB, Grid

RESET = "\x1b[0m"


def to_text(grid: Grid) -> str:
    """Characters only, no color. Trailing spaces are dropped."""
    return "\n".join("".join(cell[0] for cell in row).rstrip() for row in grid)


def to_ansi(grid: Grid) -> str:
    """24-bit color escapes, written only when the color changes.

    Each line that set a color ends with a reset, so nothing bleeds into
    the next line or the shell prompt.
    """
    lines: List[str] = []
    for row in _trim(grid):
        parts: List[str] = []
        current: Tuple[Optional[RGB], Optional[RGB]] = (None, None)
        for char, fg, bg in row:
            if (fg, bg) != current:
                parts.append(_sgr(current, fg, bg))
                current = (fg, bg)
            parts.append(char)
        if current != (None, None):
            parts.append(RESET)
        lines.append("".join(parts))
    return "\n".join(lines)


def _sgr(current: Tuple[Optional[RGB], Optional[RGB]], fg: Optional[RGB], bg: Optional[RGB]) -> str:
    old_fg, old_bg = current
    codes: List[str] = []
    # Going back to the terminal's own colors needs a reset, then set what's left
    if (old_fg is not None and fg is None) or (old_bg is not None and bg is None):
        codes.append("0")
        old_fg = old_bg = None
    if fg is not None and fg != old_fg:
        codes.append("38;2;%d;%d;%d" % fg)
    if bg is not None and bg != old_bg:
        codes.append("48;2;%d;%d;%d" % bg)
    return "\x1b[" + ";".join(codes) + "m"


def _trim(grid: Grid) -> Grid:
    """Drop blank cells (space, no background) from the end of each row."""
    trimmed: Grid = []
    for row in grid:
        end = len(row)
        while end and row[end - 1][0] == " " and row[end - 1][2] is None:
            end -= 1
        trimmed.append(row[:end])
    return trimmed


def to_html(grid: Grid, title: str = "asciify", invert: bool = False) -> str:
    """A standalone HTML page with the art in a <pre>, colored with spans."""
    background, foreground = ("#ffffff", "#000000") if invert else ("#000000", "#e6e6e6")
    lines: List[str] = []
    for row in _trim(grid):
        parts: List[str] = []
        for (fg, bg), cells in groupby(row, key=lambda cell: (cell[1], cell[2])):
            text = html.escape("".join(cell[0] for cell in cells), quote=False)
            css = []
            if fg is not None:
                css.append("color:#%02x%02x%02x" % fg)
            if bg is not None:
                css.append("background:#%02x%02x%02x" % bg)
            parts.append('<span style="%s">%s</span>' % (";".join(css), text) if css else text)
        lines.append("".join(parts))

    body = "\n".join(lines)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{html.escape(title)}</title>\n"
        "<style>\n"
        f"body {{ margin: 0; background: {background}; }}\n"
        f"pre {{ margin: 0; padding: 1em; color: {foreground}; line-height: 1;\n"
        "      font-family: 'Cascadia Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace; }}\n"
        "</style>\n</head>\n<body>\n"
        f"<pre>{body}</pre>\n"
        "</body>\n</html>\n"
    )

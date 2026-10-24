"""The ``asciify`` command."""

import argparse
import os
import shutil
import sys
import time
from typing import List, Optional, Sequence, TextIO, Tuple

from PIL import Image

from asciify import __version__
from asciify.loader import AsciifyError, frames, is_animated, open_image
from asciify.output import RESET, to_ansi, to_html, to_text
from asciify.render import MODES, Grid, render

DEFAULT_WIDTH = 100
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CLEAR_TO_EOL = "\x1b[K"


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a whole number") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _non_negative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a whole number") from None
    if number < 0:
        raise argparse.ArgumentTypeError("must be 0 or more")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asciify",
        description="Convert an image to ASCII art or colored block art in the terminal.",
    )
    parser.add_argument("image", help="image file, an http(s) URL, or - to read standard input")
    parser.add_argument("-w", "--width", type=_positive_int,
                        help="output width in characters (default: fit the terminal, or 100 when not a terminal)")
    parser.add_argument("-m", "--mode", choices=MODES, default="ascii",
                        help="ascii: characters by brightness (default); "
                             "blocks: half-block cells, twice the vertical detail")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto",
                        help="auto (default) colors terminal output unless NO_COLOR is set, "
                             "and HTML files; never colors plain text files")
    parser.add_argument("-nc", "--no-color", action="store_true", help="same as --color never")
    parser.add_argument("-i", "--invert", action="store_true",
                        help="invert brightness, for terminals with a light background")
    parser.add_argument("-c", "--chars", metavar="RAMP",
                        help="characters to use in ascii mode, from least to most ink, e.g. ' .:-=+*#%%@'")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="save to FILE instead of printing; a .html or .htm name saves a web page")
    parser.add_argument("-a", "--animate", action="store_true",
                        help="play an animated GIF or WebP in the terminal (Ctrl+C stops)")
    parser.add_argument("--loop", type=_non_negative_int, default=0, metavar="N",
                        help="with --animate, play N times (default: 0, forever)")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.chars is not None:
        if args.mode != "ascii":
            parser.error("--chars only applies to --mode ascii")
        if len(args.chars) < 2:
            parser.error("--chars needs at least 2 characters")
    if args.animate and args.output:
        parser.error("--animate plays in the terminal and can't be combined with --output")

    to_terminal = args.output is None and _stdout_is_terminal()
    if args.animate and not to_terminal:
        parser.error("--animate needs a terminal to play in")

    try:
        image = open_image(args.image)
        color = _use_color(args, to_terminal)
        width, max_rows = _size(args.width, to_terminal)

        if args.output:
            grid = render(image, width, args.mode, color, args.invert, args.chars)
            _save(args.output, grid, color, args.invert, args.image)
            return 0

        if to_terminal:
            _enable_windows_ansi()
        else:
            _utf8_stdout()

        if args.animate and is_animated(image):
            return _play(image, width, max_rows, args, color)

        grid = render(image, width, args.mode, color, args.invert, args.chars, max_rows)
        sys.stdout.write((to_ansi(grid) if color else to_text(grid)) + "\n")
        sys.stdout.flush()
        return 0
    except AsciifyError as e:
        print(f"asciify: error: {e}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # Output piped into something like `head` that stopped reading
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1
    except KeyboardInterrupt:
        return 130


def _stdout_is_terminal() -> bool:
    return sys.stdout.isatty()


def _use_color(args: argparse.Namespace, to_terminal: bool) -> bool:
    choice = "never" if args.no_color else args.color
    if choice != "auto":
        return bool(choice == "always")
    if args.output:
        return _is_html(args.output)
    return to_terminal and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"


def _size(width: Optional[int], to_terminal: bool) -> Tuple[int, Optional[int]]:
    """The width to render at, and the most rows that fit (None: no limit)."""
    if not to_terminal:
        return (width or DEFAULT_WIDTH), None
    columns, lines = shutil.get_terminal_size((DEFAULT_WIDTH, 24))
    if width is not None:
        return width, None
    return max(1, columns), max(1, lines - 1)


def _is_html(path: str) -> bool:
    return path.lower().endswith((".html", ".htm"))


def _save(path: str, grid: Grid, color: bool, invert: bool, source: str) -> None:
    if _is_html(path):
        title = "asciify: " + ("standard input" if source == "-" else os.path.basename(source.rstrip("/")))
        content = to_html(grid if color else _uncolored(grid), title, invert)
    else:
        content = (to_ansi(grid) if color else to_text(grid)) + "\n"
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except OSError as e:
        raise AsciifyError(f"cannot write {path}: {e.strerror or e}") from None


def _uncolored(grid: Grid) -> Grid:
    return [[(char, None, None) for char, _, _ in row] for row in grid]


def _play(image: Image.Image, width: int, max_rows: Optional[int], args: argparse.Namespace, color: bool,
          out: Optional[TextIO] = None) -> int:
    """Draw each frame over the previous one until the loop count runs out or Ctrl+C."""
    out = out or sys.stdout
    if max_rows is None:  # an explicit --width still has to fit, or the frames can't overwrite each other
        max_rows = max(1, shutil.get_terminal_size((DEFAULT_WIDTH, 24)).lines - 1)
    rendered: List[Tuple[str, int]] = []
    for frame, duration in frames(image):
        grid = render(frame, width, args.mode, color, args.invert, args.chars, max_rows)
        text = to_ansi(grid) if color else to_text(grid)
        rendered.append(("\n".join(line + CLEAR_TO_EOL for line in text.split("\n")), duration))

    height = rendered[0][0].count("\n") + 1
    out.write(HIDE_CURSOR)
    try:
        plays = 0
        first = True
        while args.loop == 0 or plays < args.loop:
            for text, duration in rendered:
                if not first:
                    out.write("\r" + (f"\x1b[{height - 1}A" if height > 1 else ""))
                first = False
                out.write(text)
                out.flush()
                time.sleep(duration / 1000)
            plays += 1
    except KeyboardInterrupt:
        pass
    finally:
        out.write(RESET + SHOW_CURSOR + "\n")
        out.flush()
    return 0


def _enable_windows_ansi() -> None:
    """Make Windows consoles understand ANSI escapes (a no-op elsewhere)."""
    if os.name != "nt":
        return
    try:
        import colorama
    except ImportError:
        return
    colorama.just_fix_windows_console()


def _utf8_stdout() -> None:
    """Redirected output is written as UTF-8, whatever the locale, so block characters survive."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")

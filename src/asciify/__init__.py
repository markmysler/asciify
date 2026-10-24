"""Convert images to ASCII art or colored block art for the terminal."""

__version__ = "1.1.0"

from typing import Optional  # noqa: E402

from PIL import Image  # noqa: E402

from asciify.output import to_ansi, to_html, to_text  # noqa: E402
from asciify.render import render  # noqa: E402

__all__ = ["__version__", "image_to_ascii", "convert_image_to_ascii", "render", "to_ansi", "to_html", "to_text"]


def image_to_ascii(image: Image.Image, width: int = 100, *, mode: str = "ascii", color: bool = True,
                   invert: bool = False, chars: Optional[str] = None) -> str:
    """Render a Pillow image as text: ANSI-colored if ``color``, plain otherwise."""
    grid = render(image, width, mode=mode, color=color, invert=invert, chars=chars)
    return to_ansi(grid) if color else to_text(grid)


def convert_image_to_ascii(path: str, width: int = 100, use_color: bool = True) -> str:
    """Open an image file and render it (the 1.0 API, kept for compatibility).

    Unlike 1.0, a file that can't be opened raises ``asciify.loader.AsciifyError``
    instead of returning the error message as the result.
    """
    from asciify.loader import open_image

    return image_to_ascii(open_image(path), width, color=use_color)

"""Open images from a file, standard input or a URL."""

import io
import os
import sys
import urllib.error
import urllib.request
from typing import BinaryIO, List, Optional, Tuple

from PIL import Image, ImageSequence, UnidentifiedImageError

from asciify import __version__

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
DOWNLOAD_TIMEOUT = 20
DEFAULT_FRAME_MS = 100
MIN_FRAME_MS = 20


class AsciifyError(Exception):
    """A problem worth showing the user as a one-line message."""


def is_url(source: str) -> bool:
    return source.lower().startswith(("http://", "https://"))


def read_source(source: str, stdin: Optional[BinaryIO] = None) -> bytes:
    """The raw bytes of a path, a URL, or "-" for standard input."""
    if source == "-":
        stream = stdin if stdin is not None else sys.stdin.buffer
        data = stream.read()
        if not data:
            raise AsciifyError("no image data on standard input")
        return data
    if is_url(source):
        return _download(source)
    if os.path.isdir(source):
        raise AsciifyError(f"{source} is a directory, not an image")
    try:
        with open(source, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise AsciifyError(f"no such file: {source}") from None
    except OSError as e:
        raise AsciifyError(f"cannot read {source}: {e.strerror or e}") from None


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": f"asciify/{__version__}"})
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            data: bytes = response.read(MAX_DOWNLOAD_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise AsciifyError(f"could not download {url}: HTTP {e.code} {e.reason}") from None
    except (urllib.error.URLError, OSError) as e:
        reason = getattr(e, "reason", e)
        raise AsciifyError(f"could not download {url}: {reason}") from None
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise AsciifyError(f"{url} is larger than {MAX_DOWNLOAD_BYTES // (1024 * 1024)} MB")
    return data


def open_image(source: str, stdin: Optional[BinaryIO] = None) -> Image.Image:
    """Open and decode an image. Raises AsciifyError with a readable message."""
    data = read_source(source, stdin)
    name = "standard input" if source == "-" else source
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except UnidentifiedImageError:
        raise AsciifyError(f"{name} is not an image format Pillow can read") from None
    except (OSError, ValueError, Image.DecompressionBombError) as e:
        raise AsciifyError(f"could not decode {name}: {e}") from None
    return image


def frames(image: Image.Image) -> List[Tuple[Image.Image, int]]:
    """Every frame of an animated image with its duration in ms (one frame for a still)."""
    result: List[Tuple[Image.Image, int]] = []
    for frame in ImageSequence.Iterator(image):
        duration = frame.info.get("duration") or DEFAULT_FRAME_MS
        result.append((frame.convert("RGBA"), max(MIN_FRAME_MS, int(duration))))
    return result


def is_animated(image: Image.Image) -> bool:
    return bool(getattr(image, "is_animated", False)) and getattr(image, "n_frames", 1) > 1

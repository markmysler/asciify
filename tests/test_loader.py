import io
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from asciify.loader import AsciifyError, frames, is_animated, open_image


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def server(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(tmp_path)))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_opens_a_file(image_file):
    assert open_image(image_file).size == (256, 64)


def test_missing_file(tmp_path):
    with pytest.raises(AsciifyError, match="no such file"):
        open_image(str(tmp_path / "nope.png"))


def test_directory(tmp_path):
    with pytest.raises(AsciifyError, match="is a directory"):
        open_image(str(tmp_path))


def test_not_an_image(tmp_path):
    path = tmp_path / "notes.png"
    path.write_text("hello")
    with pytest.raises(AsciifyError, match="not an image"):
        open_image(str(path))


def test_truncated_image(tmp_path, image_file):
    data = open(image_file, "rb").read()
    path = tmp_path / "cut.png"
    path.write_bytes(data[: len(data) // 2])
    with pytest.raises(AsciifyError):
        open_image(str(path))


def test_standard_input(image_file):
    with open(image_file, "rb") as f:
        assert open_image("-", stdin=io.BytesIO(f.read())).size == (256, 64)


def test_empty_standard_input():
    with pytest.raises(AsciifyError, match="standard input"):
        open_image("-", stdin=io.BytesIO(b""))


def test_url(server, image_file, tmp_path):
    assert open_image(f"{server}/gradient.png").size == (256, 64)


def test_url_not_found(server):
    with pytest.raises(AsciifyError, match="HTTP 404"):
        open_image(f"{server}/missing.png")


def test_animated_frames(animated_gif):
    image = open_image(animated_gif)
    assert is_animated(image)
    result = frames(image)
    assert [duration for _, duration in result] == [30, 40, 50]
    assert result[2][0].convert("RGB").getpixel((0, 0)) == (255, 0, 0)


def test_still_image_is_one_frame(image_file):
    image = open_image(image_file)
    assert not is_animated(image)
    assert len(frames(image)) == 1

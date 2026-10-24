import pytest
from PIL import Image, ImageDraw


@pytest.fixture
def gradient():
    """Black on the left to white on the right, 256x64."""
    image = Image.new("L", (256, 64))
    image.putdata([x for _ in range(64) for x in range(256)])
    return image.convert("RGB")


@pytest.fixture
def red_dot():
    """A red circle on a transparent background."""
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((25, 25, 75, 75), fill=(255, 0, 0, 255))
    return image


@pytest.fixture
def image_file(tmp_path, gradient):
    path = tmp_path / "gradient.png"
    gradient.save(path)
    return str(path)


@pytest.fixture
def animated_gif(tmp_path):
    path = tmp_path / "blink.gif"
    frames = [Image.new("RGB", (40, 40), c) for c in ((255, 255, 255), (0, 0, 0), (255, 0, 0))]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=[30, 40, 50], loop=0)
    return str(path)

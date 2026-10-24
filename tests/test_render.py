import pytest
from PIL import Image

from asciify.render import DETAILED_RAMP, SIMPLE_RAMP, grid_size, luminance, render, render_blocks


def chars(grid):
    return ["".join(cell[0] for cell in row) for row in grid]


class TestRamps:
    def test_ramps_have_no_duplicates(self):
        assert len(set(DETAILED_RAMP)) == len(DETAILED_RAMP) == 70
        assert len(set(SIMPLE_RAMP)) == len(SIMPLE_RAMP) == 10

    def test_ramps_start_with_a_space(self):
        assert DETAILED_RAMP[0] == SIMPLE_RAMP[0] == " "


class TestGridSize:
    def test_aspect_is_corrected_for_tall_cells(self):
        assert grid_size((200, 100), 100) == (100, 25)

    @pytest.mark.parametrize("size", [(2000, 10), (10000, 1), (1, 1)])
    def test_never_zero_rows(self, size):
        columns, rows = grid_size(size, 100)
        assert columns == 100 and rows >= 1

    def test_shrinks_to_fit_max_rows(self):
        columns, rows = grid_size((100, 1000), 80, max_rows=20)
        assert rows <= 20 and columns == 4

    @pytest.mark.parametrize("width", [0, -5])
    def test_rejects_bad_width(self, width):
        with pytest.raises(ValueError):
            grid_size((10, 10), width)


class TestAscii:
    def test_gradient_uses_the_ramp_in_order(self, gradient):
        row = chars(render(gradient, 10, color=False))[0]
        positions = [SIMPLE_RAMP.index(c) for c in row]
        assert positions == sorted(positions)
        assert row[0] == " " and row[-1] == "@"

    def test_invert_reverses_brightness(self, gradient):
        row = chars(render(gradient, 10, color=False, invert=True))[0]
        assert row[0] == "@" and row[-1] == " "

    def test_custom_chars(self, gradient):
        row = chars(render(gradient, 8, color=False, chars="ab"))[0]
        assert set(row) == {"a", "b"} and row.startswith("a") and row.endswith("b")

    def test_color_cells_carry_the_pixel_color(self):
        grid = render(Image.new("RGB", (10, 10), (10, 200, 30)), 4)
        assert all(cell[1] == (10, 200, 30) and cell[2] is None for row in grid for cell in row)

    def test_no_color_cells_have_no_color(self, gradient):
        grid = render(gradient, 20, color=False)
        assert all(cell[1] is None and cell[2] is None for row in grid for cell in row)

    def test_transparent_pixels_are_blank(self, red_dot):
        grid = render(red_dot, 20)
        assert grid[0][0] == (" ", None, None)
        middle = grid[len(grid) // 2][10]
        assert middle[1] == (255, 0, 0)

    def test_width_is_respected(self, gradient):
        assert all(len(row) == 37 for row in render(gradient, 37))

    @pytest.mark.parametrize("mode", ["L", "P", "LA", "CMYK", "I;16", "1"])
    def test_any_image_mode(self, mode):
        image = Image.new(mode, (30, 30))
        assert render(image, 10)

    def test_luminance_weights_green_over_blue(self):
        assert luminance(0, 255, 0) > luminance(255, 0, 0) > luminance(0, 0, 255)

    def test_unknown_mode(self, gradient):
        with pytest.raises(ValueError):
            render(gradient, 10, mode="braille")


class TestBlocks:
    def test_two_pixels_per_cell(self):
        image = Image.new("RGB", (2, 2))
        image.putdata([(255, 0, 0), (255, 0, 0), (0, 0, 255), (0, 0, 255)])
        grid = render(image, 2, mode="blocks")
        assert grid == [[("▀", (255, 0, 0), (0, 0, 255))] * 2]

    def test_transparent_halves(self):
        image = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
        image.putpixel((0, 1), (0, 255, 0, 255))
        image.putpixel((1, 0), (0, 0, 255, 255))
        grid = render_blocks(image)  # already one pixel per half cell
        assert grid == [[("▄", (0, 255, 0), None), ("▀", (0, 0, 255), None)]]

    def test_mono_blocks(self):
        image = Image.new("RGBA", (4, 2), (0, 0, 0, 255))
        for x, (top, bottom) in enumerate([(0, 0), (255, 0), (0, 255), (255, 255)]):
            image.putpixel((x, 0), (top, top, top, 255))
            image.putpixel((x, 1), (bottom, bottom, bottom, 255))
        assert chars(render_blocks(image, color=False)) == [" ▀▄█"]
        assert chars(render_blocks(image, color=False, invert=True)) == ["█▄▀ "]

    def test_same_rows_as_ascii_from_twice_the_pixels(self, gradient):
        assert len(render(gradient, 64, mode="blocks")) == len(render(gradient, 64))

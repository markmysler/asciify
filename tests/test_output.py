from asciify.output import RESET, to_ansi, to_html, to_text

RED = (255, 0, 0)
BLUE = (0, 0, 255)


def test_text_drops_colors_and_trailing_spaces():
    grid = [[("a", RED, None), ("b", None, None), (" ", None, None)], [(" ", None, None)]]
    assert to_text(grid) == "ab\n"


def test_ansi_only_writes_an_escape_when_the_color_changes():
    grid = [[("a", RED, None), ("b", RED, None), ("c", BLUE, None)]]
    out = to_ansi(grid)
    assert out == "\x1b[38;2;255;0;0mab\x1b[38;2;0;0;255mc" + RESET
    assert out.count("\x1b[38;2") == 2


def test_ansi_resets_at_every_line_end():
    grid = [[("a", RED, None)], [("b", RED, None)]]
    lines = to_ansi(grid).split("\n")
    assert all(line.endswith(RESET) for line in lines)
    assert lines[1].startswith("\x1b[38;2;255;0;0m")


def test_ansi_resets_before_returning_to_default_color():
    grid = [[("a", RED, BLUE), ("b", RED, None)]]
    assert to_ansi(grid) == "\x1b[38;2;255;0;0;48;2;0;0;255ma\x1b[0;38;2;255;0;0mb" + RESET


def test_ansi_plain_grid_has_no_escapes():
    assert "\x1b" not in to_ansi([[("a", None, None), ("b", None, None)]])


def test_ansi_trims_blank_cells_but_keeps_backgrounds():
    grid = [[("a", RED, None), (" ", None, None)], [(" ", None, BLUE)]]
    assert to_ansi(grid).split("\n") == ["\x1b[38;2;255;0;0ma" + RESET, "\x1b[48;2;0;0;255m " + RESET]


def test_html_escapes_and_merges_runs():
    grid = [[("<", RED, None), ("&", RED, None), (">", None, None)]]
    page = to_html(grid, title="a <test>")
    assert '<span style="color:#ff0000">&lt;&amp;</span>&gt;' in page
    assert "<title>a &lt;test&gt;</title>" in page


def test_html_backgrounds_and_invert():
    page = to_html([[("▀", RED, BLUE)]], invert=True)
    assert "color:#ff0000;background:#0000ff" in page
    assert "background: #ffffff" in page

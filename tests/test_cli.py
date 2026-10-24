import io
import os
import sys

import pytest
from PIL import Image

import asciify
from asciify import cli
from asciify.cli import main


@pytest.fixture
def terminal(monkeypatch, capsys):
    """Pretend stdout is an 80x24 terminal, and don't wait between frames."""
    monkeypatch.setattr(cli, "_stdout_is_terminal", lambda: True)
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda fallback=None: os.terminal_size((80, 24)))
    monkeypatch.setattr(cli.time, "sleep", lambda seconds: None)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)


def test_default_output_when_piped_is_plain_text_100_wide(image_file, capsys):
    assert main([image_file]) == 0
    out = capsys.readouterr().out
    assert "\x1b" not in out
    assert max(len(line) for line in out.splitlines()) == 100


def test_width(image_file, capsys):
    assert main([image_file, "-w", "40"]) == 0
    assert max(len(line) for line in capsys.readouterr().out.splitlines()) == 40


@pytest.mark.parametrize("width", ["0", "-5", "abc"])
def test_bad_width_is_a_usage_error(image_file, width, capsys):
    with pytest.raises(SystemExit) as exc:
        main([image_file, "-w", width])
    assert exc.value.code == 2
    assert "--width" in capsys.readouterr().err


def test_missing_file_fails_on_stderr(tmp_path, capsys):
    assert main([str(tmp_path / "nope.png")]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("asciify: error: no such file")


def test_very_wide_image_does_not_crash(tmp_path, capsys):
    path = tmp_path / "banner.png"
    Image.new("RGB", (2000, 10), (128, 128, 128)).save(path)
    assert main([str(path)]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 1


def test_color_always(image_file, capsys):
    main([image_file, "--color", "always", "-w", "20"])
    assert "\x1b[38;2;" in capsys.readouterr().out


def test_terminal_gets_color_and_fits(image_file, terminal, capsys):
    main([image_file])
    out = capsys.readouterr().out
    assert "\x1b[38;2;" in out
    lines = out.splitlines()
    assert len(lines) <= 23


@pytest.mark.parametrize("flags", [["-nc"], ["--no-color"], ["--color", "never"]])
def test_no_color_flags(image_file, terminal, capsys, flags):
    main([image_file, *flags])
    assert "\x1b" not in capsys.readouterr().out


def test_no_color_env(image_file, terminal, monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    main([image_file])
    assert "\x1b" not in capsys.readouterr().out


def test_tall_image_fits_the_terminal(tmp_path, terminal, capsys):
    path = tmp_path / "tall.png"
    Image.new("RGB", (100, 2000), (200, 200, 200)).save(path)
    main([str(path), "-nc"])
    assert len(capsys.readouterr().out.splitlines()) <= 23


def test_blocks_mode(image_file, capsys):
    main([image_file, "-m", "blocks", "--color", "always", "-w", "30"])
    out = capsys.readouterr().out
    assert "▀" in out and ";48;2;" in out


def test_invert_and_chars(image_file, capsys):
    main([image_file, "-w", "10", "--chars", "ab", "--invert"])
    row = capsys.readouterr().out.splitlines()[0]
    assert row.startswith("b") and row.endswith("a")


def test_chars_needs_ascii_mode(image_file, capsys):
    with pytest.raises(SystemExit):
        main([image_file, "-m", "blocks", "--chars", "ab"])
    assert "--chars only applies" in capsys.readouterr().err


def test_save_text(image_file, tmp_path):
    out = tmp_path / "art.txt"
    assert main([image_file, "-w", "30", "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "\x1b" not in text and max(len(line) for line in text.splitlines()) == 30


def test_save_ansi(image_file, tmp_path):
    out = tmp_path / "art.ans"
    main([image_file, "-w", "30", "-o", str(out), "--color", "always"])
    assert "\x1b[38;2;" in out.read_text(encoding="utf-8")


def test_save_html(image_file, tmp_path):
    out = tmp_path / "art.html"
    main([image_file, "-w", "30", "-o", str(out)])
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!DOCTYPE html>") and "<title>asciify: gradient.png</title>" in page
    assert "color:#" in page


def test_save_html_without_color(image_file, tmp_path):
    out = tmp_path / "art.html"
    main([image_file, "-o", str(out), "-nc"])
    assert "<span" not in out.read_text(encoding="utf-8")


def test_save_to_bad_path(image_file, tmp_path, capsys):
    assert main([image_file, "-o", str(tmp_path / "no" / "such" / "dir.txt")]) == 1
    assert "cannot write" in capsys.readouterr().err


def test_standard_input(image_file, monkeypatch, capsys):
    with open(image_file, "rb") as f:
        data = f.read()
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data)))
    assert main(["-", "-w", "20"]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 3


def test_animate_plays_every_frame(animated_gif, terminal, capsys):
    assert main([animated_gif, "--animate", "--loop", "2", "-nc"]) == 0
    out = capsys.readouterr().out
    assert out.startswith(cli.HIDE_CURSOR) and out.rstrip("\n").endswith(cli.SHOW_CURSOR)
    # 3 frames twice; every frame after the first moves the cursor back up first
    assert out.count("\r\x1b[") == 5


def test_animate_needs_a_terminal(animated_gif, capsys):
    with pytest.raises(SystemExit):
        main([animated_gif, "--animate"])
    assert "needs a terminal" in capsys.readouterr().err


def test_animate_stops_cleanly_on_ctrl_c(animated_gif, terminal, monkeypatch, capsys):
    def interrupt(seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.time, "sleep", interrupt)
    assert main([animated_gif, "--animate"]) == 0
    assert capsys.readouterr().out.rstrip("\n").endswith(cli.SHOW_CURSOR)


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out.strip() == f"asciify {asciify.__version__}"


def test_python_api(gradient):
    text = asciify.image_to_ascii(gradient, 10, color=False)
    assert text.splitlines()[0][-1] == "@"
    assert "\x1b[38;2;" in asciify.image_to_ascii(gradient, 10)


def test_old_api_still_works(image_file):
    assert asciify.convert_image_to_ascii(image_file, 20, use_color=False).count("\n") == 2

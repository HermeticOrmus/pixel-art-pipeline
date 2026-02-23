"""Tests for frame assembly (GIF creation, static fallbacks)."""

import base64

import pytest
from PIL import Image

from pixelart.assembler import (
    create_static_fallback,
    frames_to_gif,
    save_frames,
    save_frames_offset,
)


def _make_frame_data(width=64, height=64, color=(255, 0, 0, 255)) -> dict:
    """Create a base64-encoded frame dict for testing."""
    import io

    img = Image.new("RGBA", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"type": "base64", "base64": b64, "format": "png"}


def _create_frame_files(frame_dir, count=16, size=64):
    """Create numbered frame PNGs in a directory."""
    frame_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        img = Image.new("RGBA", (size, size), (255, i * 15, 0, 255))
        img.save(frame_dir / f"frame_{i:02d}.png")


class TestSaveFrames:
    def test_save_frames(self, tmp_path):
        frames = [_make_frame_data(color=(255, 0, 0, 255)) for _ in range(4)]
        output_dir = tmp_path / "frames"

        paths = save_frames(frames, output_dir)

        assert len(paths) == 4
        assert all(p.exists() for p in paths)
        assert paths[0].name == "frame_00.png"
        assert paths[3].name == "frame_03.png"

    def test_save_frames_creates_directory(self, tmp_path):
        frames = [_make_frame_data()]
        output_dir = tmp_path / "deep" / "nested" / "dir"

        paths = save_frames(frames, output_dir)

        assert output_dir.exists()
        assert len(paths) == 1

    def test_save_frames_offset(self, tmp_path):
        frames = [_make_frame_data() for _ in range(4)]
        output_dir = tmp_path / "frames"

        paths = save_frames_offset(frames, output_dir, offset=16)

        assert len(paths) == 4
        assert paths[0].name == "frame_16.png"
        assert paths[3].name == "frame_19.png"


class TestFramesToGif:
    def test_creates_gif(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=4)

        gif_path = tmp_path / "output.gif"
        result = frames_to_gif(frame_dir, gif_path)

        assert result == gif_path
        assert gif_path.exists()
        assert gif_path.stat().st_size > 0

    def test_gif_is_animated(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=4)

        gif_path = tmp_path / "output.gif"
        frames_to_gif(frame_dir, gif_path)

        with Image.open(gif_path) as gif:
            assert gif.n_frames == 4

    def test_gif_upscale(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=2, size=32)

        gif_path = tmp_path / "output.gif"
        frames_to_gif(frame_dir, gif_path, upscale_size=256)

        with Image.open(gif_path) as gif:
            assert gif.size == (256, 256)

    def test_no_frames_returns_none(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = frames_to_gif(empty_dir, tmp_path / "output.gif")
        assert result is None

    def test_custom_duration(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=2)

        gif_path = tmp_path / "output.gif"
        frames_to_gif(frame_dir, gif_path, duration_ms=100)

        with Image.open(gif_path) as gif:
            assert gif.info.get("duration") == 100

    def test_creates_parent_directories(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=2)

        gif_path = tmp_path / "deep" / "nested" / "output.gif"
        result = frames_to_gif(frame_dir, gif_path)

        assert result == gif_path
        assert gif_path.exists()


class TestStaticFallback:
    def test_creates_static_png(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=16)

        static_path = tmp_path / "static.png"
        result = create_static_fallback(frame_dir, static_path)

        assert result == static_path
        assert static_path.exists()

    def test_default_frame_15(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=16)

        static_path = tmp_path / "static.png"
        create_static_fallback(frame_dir, static_path)

        # frame_15 has color (255, 225, 0, 255)
        with Image.open(static_path) as img:
            pixel = img.getpixel((0, 0))
            assert pixel[1] == 225  # 15 * 15

    def test_custom_frame_index(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=16)

        static_path = tmp_path / "static.png"
        create_static_fallback(frame_dir, static_path, frame_index=0)

        with Image.open(static_path) as img:
            pixel = img.getpixel((0, 0))
            assert pixel[1] == 0  # frame 0 has 0 * 15

    def test_upscale_size(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=16, size=32)

        static_path = tmp_path / "static.png"
        create_static_fallback(frame_dir, static_path, upscale_size=256)

        with Image.open(static_path) as img:
            assert img.size == (256, 256)

    def test_fallback_to_last_frame(self, tmp_path):
        frame_dir = tmp_path / "frames"
        _create_frame_files(frame_dir, count=4)  # Only 4 frames, no frame_15

        static_path = tmp_path / "static.png"
        result = create_static_fallback(frame_dir, static_path)

        assert result == static_path
        assert static_path.exists()

    def test_no_frames_returns_none(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = create_static_fallback(empty_dir, tmp_path / "static.png")
        assert result is None

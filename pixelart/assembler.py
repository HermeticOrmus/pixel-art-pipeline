"""Frame assembly: PNG frames to animated GIFs and static fallbacks."""

import base64
from pathlib import Path

from PIL import Image


def save_frames(frames: list[dict], output_dir: Path) -> list[Path]:
    """Save base64-encoded frames as numbered PNG files.

    Args:
        frames: List of dicts with 'base64' key containing frame data.
        output_dir: Directory to write frame_00.png, frame_01.png, etc.

    Returns:
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, frame in enumerate(frames):
        path = output_dir / f"frame_{i:02d}.png"
        with open(path, "wb") as f:
            f.write(base64.b64decode(frame["base64"]))
        paths.append(path)
    return paths


def save_frames_offset(frames: list[dict], output_dir: Path, offset: int) -> list[Path]:
    """Save frames starting at a given index (for emotes that continue numbering).

    Args:
        frames: List of dicts with 'base64' key.
        output_dir: Directory to write frames.
        offset: Starting frame number (e.g. 16 for frame_16.png).

    Returns:
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, frame in enumerate(frames):
        path = output_dir / f"frame_{i + offset:02d}.png"
        with open(path, "wb") as f:
            f.write(base64.b64decode(frame["base64"]))
        paths.append(path)
    return paths


def frames_to_gif(
    frame_dir: Path,
    output_path: Path,
    upscale_size: int = 512,
    duration_ms: int = 200,
    frame_pattern: str = "frame_*.png",
) -> Path | None:
    """Assemble PNG frames into an animated GIF.

    Args:
        frame_dir: Directory containing numbered frame PNGs.
        output_path: Where to write the output GIF.
        upscale_size: Target size for nearest-neighbor upscale (default 512).
        duration_ms: Milliseconds per frame (default 200 = 5 FPS).
        frame_pattern: Glob pattern for frame files.

    Returns:
        Output path if successful, None if no frames found.
    """
    frame_files = sorted(frame_dir.glob(frame_pattern))
    if not frame_files:
        return None

    frames = [Image.open(f) for f in frame_files]

    # Upscale with nearest neighbor to preserve crisp pixel art
    upscaled = [f.resize((upscale_size, upscale_size), Image.NEAREST) for f in frames]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    upscaled[0].save(
        output_path,
        save_all=True,
        append_images=upscaled[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
        disposal=2,  # Clear canvas before each frame (prevents ghosting)
    )

    return output_path


def create_static_fallback(
    frame_dir: Path,
    output_path: Path,
    upscale_size: int = 512,
    frame_index: int = 15,
) -> Path | None:
    """Extract a single frame and upscale as static PNG fallback.

    Args:
        frame_dir: Directory containing numbered frame PNGs.
        output_path: Where to write the static PNG.
        upscale_size: Target size for nearest-neighbor upscale.
        frame_index: Which frame to extract (default 15, the last of 16).

    Returns:
        Output path if successful, None if no frames found.
    """
    frame_file = frame_dir / f"frame_{frame_index:02d}.png"
    if not frame_file.exists():
        # Fall back to last available frame
        frames = sorted(frame_dir.glob("frame_*.png"))
        if not frames:
            return None
        frame_file = frames[-1]

    img = Image.open(frame_file)
    upscaled = img.resize((upscale_size, upscale_size), Image.NEAREST)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    upscaled.save(output_path)

    return output_path

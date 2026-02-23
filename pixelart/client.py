"""PixelLab API client for generating pixel art animations."""

import base64
import os
from pathlib import Path

import requests

API_BASE = "https://api.pixellab.ai/v2"


def _get_api_key() -> str:
    key = os.environ.get("PIXELLAB_API_KEY")
    if not key:
        raise RuntimeError(
            "PIXELLAB_API_KEY environment variable is not set.\n"
            "Get your API key at https://pixellab.ai and set it:\n"
            "  export PIXELLAB_API_KEY=your-key-here"
        )
    return key


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }


def encode_image(path: Path) -> dict:
    """Read a PNG file and return a base64-encoded image dict for the API."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {"type": "base64", "base64": b64, "format": "png"}


def check_balance() -> dict:
    """Check current PixelLab credit balance.

    Returns dict with 'credits_usd', 'generations_used', 'generations_total'.
    """
    r = requests.get(f"{API_BASE}/balance", headers=_get_headers(), timeout=10)
    r.raise_for_status()

    data = r.json()
    credits = data.get("credits", {})
    sub = data.get("subscription", {})

    return {
        "credits_usd": credits.get("usd", 0),
        "generations_used": sub.get("generations", 0),
        "generations_total": sub.get("total", 0),
    }


def generate_animation(
    reference_path: Path,
    action: str,
    width: int = 64,
    height: int = 64,
    seed: int | None = None,
) -> tuple[list[dict], float]:
    """Generate a 16-frame animation via PixelLab v2 API.

    Args:
        reference_path: Path to the reference PNG image.
        action: Text prompt describing the animation action.
        width: Frame width in pixels (default 64).
        height: Frame height in pixels (default 64).
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (list of frame dicts with base64 data, cost in USD).
    """
    image_data = encode_image(reference_path)

    payload = {
        "reference_image": image_data,
        "reference_image_size": {"width": width, "height": height},
        "image_size": {"width": width, "height": height},
        "action": action,
    }
    if seed is not None:
        payload["seed"] = seed

    r = requests.post(
        f"{API_BASE}/animate-with-text-v2",
        headers=_get_headers(),
        json=payload,
        timeout=300,
    )

    if r.status_code != 200:
        raise RuntimeError(f"PixelLab API error {r.status_code}: {r.text[:300]}")

    data = r.json()
    usage = data.get("usage", {})
    cost = usage.get("usd", 0)

    return data.get("images", []), cost

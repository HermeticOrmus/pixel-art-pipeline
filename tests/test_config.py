"""Tests for config loading and validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from pixelart.config import PipelineConfig, load_config


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal valid project in a temp directory."""
    # Create a 1x1 PNG reference image (minimal valid PNG)
    from PIL import Image

    ref = tmp_path / "reference.png"
    img = Image.new("RGBA", (64, 64), (255, 215, 0, 255))
    img.save(ref)

    config_data = {
        "project": {
            "name": "test-project",
            "reference": "reference.png",
            "output_dir": "./output",
            "frame_size": 64,
            "upscale_size": 512,
            "frame_duration_ms": 200,
        },
        "singles": {
            "flame": {"prompt": "transforms into a flame"},
            "star": {"prompt": "transforms into a star"},
        },
        "emotes": {
            "flame": {"prompt": "flame sways gently"},
        },
        "chains": {
            "flame_to_heart": {
                "label": "Fire to Love",
                "steps": [
                    {"from": "reference", "to": "flame", "prompt": "becomes a flame"},
                    {"from": "flame", "to": "heart", "prompt": "becomes a heart"},
                ],
            }
        },
        "journeys": {
            "hero": {
                "label": "Hero",
                "steps": [
                    {"from": "reference", "to": "sword", "prompt": "becomes sword"},
                    {"from": "sword", "to": "mushroom", "prompt": "becomes mushroom"},
                    {"from": "mushroom", "to": "crown", "prompt": "becomes crown"},
                ],
            }
        },
        "cycles": {
            "cycle_flame": {
                "shape": "flame",
                "forward_prompt": "becomes a flame",
                "reverse_prompt": "flame returns to gold",
            }
        },
    }

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config_data))

    return tmp_path, config_path


def test_load_config(tmp_project):
    _, config_path = tmp_project
    config = load_config(config_path)

    assert config.name == "test-project"
    assert config.frame_size == 64
    assert config.upscale_size == 512
    assert config.frame_duration_ms == 200


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")


def test_load_config_invalid_yaml(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text("")
    with pytest.raises(ValueError):
        load_config(bad)


def test_validate_valid(tmp_project):
    _, config_path = tmp_project
    config = load_config(config_path)
    errors = config.validate()
    assert errors == []


def test_validate_missing_reference(tmp_path):
    config_data = {
        "project": {
            "name": "test",
            "reference": "nonexistent.png",
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config_data))

    config = load_config(config_path)
    errors = config.validate()
    assert any("Reference image not found" in e for e in errors)


def test_validate_bad_frame_size(tmp_project):
    tmp_path, _ = tmp_project

    config_data = {
        "project": {
            "name": "test",
            "reference": "reference.png",
            "frame_size": 8,
        },
    }
    config_path = tmp_path / "config2.yaml"
    config_path.write_text(yaml.dump(config_data))

    config = load_config(config_path)
    errors = config.validate()
    assert any("frame_size" in e for e in errors)


def test_validate_missing_prompt(tmp_project):
    tmp_path, _ = tmp_project

    config_data = {
        "project": {
            "name": "test",
            "reference": "reference.png",
        },
        "singles": {
            "flame": {},  # Missing prompt
        },
    }
    config_path = tmp_path / "config3.yaml"
    config_path.write_text(yaml.dump(config_data))

    config = load_config(config_path)
    errors = config.validate()
    assert any("singles.flame" in e and "prompt" in e for e in errors)


def test_count_animations(tmp_project):
    _, config_path = tmp_project
    config = load_config(config_path)
    counts = config.count_animations()

    assert counts["singles"] == 2
    assert counts["emotes"] == 1
    assert counts["chains"] == 2  # 2 steps
    assert counts["journeys"] == 3  # 3 steps
    assert counts["cycles"] == 1
    assert counts["total_api_calls"] == 9


def test_estimate_cost(tmp_project):
    _, config_path = tmp_project
    config = load_config(config_path)
    cost = config.estimate_cost()

    # 9 API calls * $0.16 = $1.44
    assert abs(cost - 1.44) < 0.01


def test_path_resolution(tmp_project):
    tmp_path, config_path = tmp_project
    config = load_config(config_path)

    assert config.reference == (tmp_path / "reference.png").resolve()
    assert config.output_dir == (tmp_path / "output").resolve()


def test_directory_properties(tmp_project):
    _, config_path = tmp_project
    config = load_config(config_path)

    assert config.singles_dir == config.output_dir / "singles"
    assert config.emotes_dir == config.output_dir / "emotes"
    assert config.chains_dir == config.output_dir / "chains"
    assert config.journeys_dir == config.output_dir / "journeys"
    assert config.cycles_dir == config.output_dir / "cycles"
    assert config.static_dir == config.output_dir / "static"


def test_defaults(tmp_path):
    """Config with minimal fields should have sensible defaults."""
    from PIL import Image

    ref = tmp_path / "reference.png"
    Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(ref)

    config_data = {
        "project": {
            "name": "minimal",
            "reference": "reference.png",
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config_data))

    config = load_config(config_path)
    assert config.frame_size == 64
    assert config.upscale_size == 512
    assert config.frame_duration_ms == 200
    assert config.singles == {}
    assert config.emotes == {}

"""YAML configuration loader and validation for pixel art pipelines."""

from pathlib import Path

import yaml


class PipelineConfig:
    """Parsed and validated pipeline configuration."""

    def __init__(self, data: dict, config_dir: Path):
        self._data = data
        self._config_dir = config_dir

        project = data.get("project", {})
        self.name: str = project.get("name", "untitled")
        self.frame_size: int = project.get("frame_size", 64)
        self.upscale_size: int = project.get("upscale_size", 512)
        self.frame_duration_ms: int = project.get("frame_duration_ms", 200)

        # Resolve paths relative to config file location
        ref = project.get("reference", "reference.png")
        self.reference: Path = (config_dir / ref).resolve()

        out = project.get("output_dir", "./output")
        self.output_dir: Path = (config_dir / out).resolve()

        # Animation definitions
        self.singles: dict[str, dict] = data.get("singles", {})
        self.emotes: dict[str, dict] = data.get("emotes", {})
        self.chains: dict[str, dict] = data.get("chains", {})
        self.journeys: dict[str, dict] = data.get("journeys", {})
        self.cycles: dict[str, dict] = data.get("cycles", {})

    @property
    def singles_dir(self) -> Path:
        return self.output_dir / "singles"

    @property
    def emotes_dir(self) -> Path:
        return self.output_dir / "emotes"

    @property
    def chains_dir(self) -> Path:
        return self.output_dir / "chains"

    @property
    def journeys_dir(self) -> Path:
        return self.output_dir / "journeys"

    @property
    def cycles_dir(self) -> Path:
        return self.output_dir / "cycles"

    @property
    def static_dir(self) -> Path:
        return self.output_dir / "static"

    def validate(self) -> list[str]:
        """Validate config and return list of errors (empty = valid)."""
        errors = []

        if not self.reference.exists():
            errors.append(f"Reference image not found: {self.reference}")

        if self.frame_size < 16 or self.frame_size > 256:
            errors.append(f"frame_size must be 16-256, got {self.frame_size}")

        if self.upscale_size < self.frame_size:
            errors.append(
                f"upscale_size ({self.upscale_size}) must be >= frame_size ({self.frame_size})"
            )

        if self.frame_duration_ms < 10:
            errors.append(f"frame_duration_ms must be >= 10, got {self.frame_duration_ms}")

        # Validate singles have prompts
        for name, entry in self.singles.items():
            if not entry.get("prompt"):
                errors.append(f"singles.{name}: missing 'prompt'")

        # Validate emotes have prompts
        for name, entry in self.emotes.items():
            if not entry.get("prompt"):
                errors.append(f"emotes.{name}: missing 'prompt'")

        # Validate chains have steps
        for name, entry in self.chains.items():
            steps = entry.get("steps", [])
            if len(steps) < 2:
                errors.append(f"chains.{name}: needs at least 2 steps")
            for i, step in enumerate(steps):
                if not step.get("prompt"):
                    errors.append(f"chains.{name}.steps[{i}]: missing 'prompt'")

        # Validate journeys have steps
        for name, entry in self.journeys.items():
            steps = entry.get("steps", [])
            if len(steps) < 2:
                errors.append(f"journeys.{name}: needs at least 2 steps")
            for i, step in enumerate(steps):
                if not step.get("prompt"):
                    errors.append(f"journeys.{name}.steps[{i}]: missing 'prompt'")

        # Validate cycles
        for name, entry in self.cycles.items():
            if not entry.get("shape"):
                errors.append(f"cycles.{name}: missing 'shape'")
            if not entry.get("forward_prompt"):
                errors.append(f"cycles.{name}: missing 'forward_prompt'")
            if not entry.get("reverse_prompt"):
                errors.append(f"cycles.{name}: missing 'reverse_prompt'")

        return errors

    def count_animations(self) -> dict[str, int]:
        """Count total animations and API calls by type."""
        counts = {
            "singles": len(self.singles),
            "emotes": len(self.emotes),
            "chains": sum(len(c.get("steps", [])) for c in self.chains.values()),
            "journeys": sum(len(j.get("steps", [])) for j in self.journeys.values()),
            "cycles": len(self.cycles),  # 1 reverse call each (forward reused)
        }
        counts["total_api_calls"] = (
            counts["singles"]
            + counts["emotes"]
            + counts["chains"]
            + counts["journeys"]
            + counts["cycles"]
        )
        return counts

    def estimate_cost(self) -> float:
        """Estimate total cost in USD (~$0.16 per 16-frame generation)."""
        counts = self.count_animations()
        return counts["total_api_calls"] * 0.16


def load_config(config_path: str | Path) -> PipelineConfig:
    """Load and parse a YAML config file.

    Args:
        config_path: Path to the config.yaml file.

    Returns:
        Validated PipelineConfig instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config has validation errors.
    """
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data or not isinstance(data, dict):
        raise ValueError(f"Invalid config file: {config_path}")

    config = PipelineConfig(data, config_path.parent)
    return config

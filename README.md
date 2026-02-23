# pixel-art-pipeline

Batch pixel art animation generator using the [PixelLab API](https://pixellab.ai). Generate, assemble, and manage sprite animations from YAML config files.

Define your animations in a config file, and the pipeline handles batching, frame assembly, GIF creation, cost estimation, and resume-on-failure — all from the command line.

## Quick Start

```bash
pip install pixel-art-pipeline

# Set your PixelLab API key
export PIXELLAB_API_KEY=your-key-here

# Create a starter project
pixelart init --name my-sprites

# Preview the cost
pixelart cost --config my-sprites/config.yaml

# Generate animations
pixelart generate --config my-sprites/config.yaml
```

## Installation

```bash
# From PyPI
pip install pixel-art-pipeline

# From source
git clone https://github.com/HermeticOrmus/pixel-art-pipeline.git
cd pixel-art-pipeline
pip install -e .
```

Requires Python 3.10+ and a [PixelLab API key](https://pixellab.ai).

## Commands

| Command | Description |
|---------|-------------|
| `pixelart init --name project` | Create a starter config and reference image |
| `pixelart generate --config config.yaml` | Generate animations from config |
| `pixelart generate -c config.yaml -t singles` | Generate only singles |
| `pixelart generate -c config.yaml -t singles -n flame star` | Generate specific animations |
| `pixelart assemble --config config.yaml` | Re-assemble existing frames into GIFs |
| `pixelart cost --config config.yaml` | Estimate cost without calling the API |
| `pixelart balance` | Check your PixelLab credit balance |

## Config Format

Animations are defined in a YAML file. Here's the structure:

```yaml
project:
  name: "my-project"
  reference: "reference.png"     # Starting image (64x64 PNG)
  output_dir: "./output"
  frame_size: 64                 # API generation size
  upscale_size: 512              # GIF/PNG output size (nearest-neighbor)
  frame_duration_ms: 200         # 5 FPS

singles:
  flame:
    prompt: "golden circle transforms into a dancing flame"
  star:
    prompt: "golden circle transforms into a twinkling star"

emotes:
  flame:
    prompt: "a golden flame sways gently left and right"
    # Uses singles/flame/frame_15.png as reference automatically

chains:
  flame_to_heart:
    label: "Fire to Love"
    steps:
      - from: reference
        to: flame
        prompt: "golden circle transforms into a dancing flame"
      - from: flame
        to: heart
        prompt: "the flame reshapes into a glowing heart"

journeys:
  hero:
    label: "The Hero's Journey"
    steps:
      - from: reference
        to: sword
        prompt: "golden circle transforms into a sword"
      - from: sword
        to: mushroom
        prompt: "sword melts into a mushroom"
      - from: mushroom
        to: crown
        prompt: "mushroom stretches into a crown"

cycles:
  cycle_flame:
    shape: flame
    forward_prompt: "golden circle transforms into a dancing flame"
    reverse_prompt: "flame dissolves back into a golden circle"
```

## Animation Types

| Type | Frames | Description |
|------|--------|-------------|
| **Singles** | 16 | Reference image transforms into a shape via text prompt |
| **Emotes** | 16 | Shape performs an action (uses last single frame as reference) |
| **Chains** | 32 | 2-step sequence: A → B → C |
| **Journeys** | 48-80 | 3-5 step multi-stage narratives |
| **Cycles** | 32 | Forward + reverse for a perfect loop (A → B → A) |

## Output Structure

```
output/
├── singles/
│   ├── flame/
│   │   ├── frame_00.png ... frame_15.png
│   │   └── frame_16.png ... frame_31.png  (if emotes generated)
│   └── flame.gif
├── chains/
│   ├── flame_to_heart/
│   │   └── frame_00.png ... frame_31.png
│   └── flame_to_heart.gif
├── cycles/
│   └── ...
├── journeys/
│   └── ...
└── static/
    ├── flame.png    (upscaled last frame)
    └── ...
```

## Cost Estimation

Each 16-frame generation costs approximately **$0.16 USD**.

| Type | API Calls | Cost |
|------|-----------|------|
| 1 single | 1 | ~$0.16 |
| 1 emote | 1 | ~$0.16 |
| 1 chain (2 steps) | 2 | ~$0.32 |
| 1 journey (4 steps) | 4 | ~$0.64 |
| 1 cycle | 1 (reuses forward) | ~$0.16 |

Use `pixelart cost --config config.yaml` to preview before generating.

## Resume on Failure

The pipeline automatically skips animations that already have their expected number of frames. If a batch is interrupted (network error, API timeout), just re-run the same command — it picks up where it left off.

## Examples

The `examples/` directory includes:

- **`liquid-gold/`** — Full 114-animation config (the original project that spawned this tool)
- **`starter/`** — 5 simple animations to get started (~$1.76 total)

## Development

```bash
git clone https://github.com/HermeticOrmus/pixel-art-pipeline.git
cd pixel-art-pipeline
pip install -e ".[dev]"
ruff check pixelart/
pytest
```

## License

MIT

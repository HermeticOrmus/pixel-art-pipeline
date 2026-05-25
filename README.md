> *"Every pixel is an atom of intention. Arrange them with purpose, and static images become living transformations."*

<p align="center">
  <img src="https://ormus.solutions/mascot/golden_swan.gif" alt="pixel-art-pipeline" width="128" style="image-rendering: pixelated;" />
</p>

<h1 align="center">pixel-art-pipeline</h1>

<p align="center">
  <em>Batch pixel art animation generator using PixelLab API. Generate, assemble, and manage sprite animations from YAML configs.</em>
</p>

<p align="center">
  <a href="https://github.com/HermeticOrmus/pixel-art-pipeline/stargazers"><img src="https://img.shields.io/github/stars/HermeticOrmus/pixel-art-pipeline?style=flat-square&color=aa8142" alt="Stars" /></a>
  <a href="https://github.com/HermeticOrmus/pixel-art-pipeline/blob/main/LICENSE"><img src="https://img.shields.io/github/license/HermeticOrmus/pixel-art-pipeline?style=flat-square&color=aa8142" alt="License" /></a>
  <a href="https://github.com/HermeticOrmus/pixel-art-pipeline/commits"><img src="https://img.shields.io/github/last-commit/HermeticOrmus/pixel-art-pipeline?style=flat-square&color=aa8142" alt="Last Commit" /></a>
  <img src="https://img.shields.io/badge/Claude_Code-aa8142?style=flat-square&logo=anthropic&logoColor=white" alt="Claude Code" />
</p>

---
Batch pixel art animation generator using the [PixelLab API](https://pixellab.ai). Generate, assemble, and manage sprite animations from YAML config files.

Define your animations in a config file, and the pipeline handles batching, frame assembly, GIF creation, cost estimation, and resume-on-failure -- all from the command line.

---

## The Problem

People make one-off PixelLab API calls manually. No batch processing, no resume-on-failure, no cost estimation. Generating 76+ animations means 76+ manual API calls -- each one requiring you to set parameters, wait, download frames, assemble GIFs, and track what succeeded and what didn't.

## The Solution

A YAML config file defines all your animations. The pipeline handles batching, frame assembly, resume, and cost estimation. One command generates everything. If it fails halfway, re-run the same command and it picks up where it left off.

---

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

The pipeline automatically skips animations that already have their expected number of frames. If a batch is interrupted (network error, API timeout), just re-run the same command -- it picks up where it left off.

## Examples

The `examples/` directory includes:

- **`liquid-gold/`** -- Full 114-animation config (the original project that spawned this tool)
- **`starter/`** -- 5 simple animations to get started (~$1.76 total)

## Development

```bash
git clone https://github.com/HermeticOrmus/pixel-art-pipeline.git
cd pixel-art-pipeline
pip install -e ".[dev]"
ruff check pixelart/
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We follow the Gold Hat philosophy: every contribution should empower users, never extract from them.

## License

MIT + Gold Hat Addendum. See [LICENSE](LICENSE).

---

> *"As above, so below. As the code, so the consciousness."*
>
> **-- Hermetic Ormus, Gold Hat Technologist**

---

## Part of the Libre Open-Source Stack for Claude Code

This repository is part of a growing family of open-source toolkits for Claude Code.

### Libre suite — comprehensive plugin bundles

- [LibreUIUX-Claude-Code](https://github.com/HermeticOrmus/LibreUIUX-Claude-Code) — UI/UX development (152 agents, 70 plugins, 76 commands, 74 skills)
- [LibreArch-Claude-Code](https://github.com/HermeticOrmus/LibreArch-Claude-Code) — Software architecture and system design
- [LibreCopy-Claude-Code](https://github.com/HermeticOrmus/LibreCopy-Claude-Code) — Technical writing and documentation engineering
- [LibreDevOps-Claude-Code](https://github.com/HermeticOrmus/LibreDevOps-Claude-Code) — DevOps engineering and infrastructure automation
- [LibreEmbed-Claude-Code](https://github.com/HermeticOrmus/LibreEmbed-Claude-Code) — Embedded systems, firmware, and IoT development
- [LibreFinTech-Claude-Code](https://github.com/HermeticOrmus/LibreFinTech-Claude-Code) — Financial technology development
- [LibreGEO-Claude-Code](https://github.com/HermeticOrmus/LibreGEO-Claude-Code) — AI-search optimization (ChatGPT, Perplexity, Gemini, Google AI Overviews)
- [LibreGameDev-Claude-Code](https://github.com/HermeticOrmus/LibreGameDev-Claude-Code) — Game development across Godot, Unity, Unreal
- [LibreMLOps-Claude-Code](https://github.com/HermeticOrmus/LibreMLOps-Claude-Code) — ML engineering and AI operations
- [LibreMobileDev-Claude-Code](https://github.com/HermeticOrmus/LibreMobileDev-Claude-Code) — Mobile app development (Flutter, React Native, native iOS, native Android)
- [LibreSecOps-Claude-Code](https://github.com/HermeticOrmus/LibreSecOps-Claude-Code) — Security operations

### Skills mini-repos — single CLAUDE.md drop-ins

- [vibe-engineer-skills](https://github.com/HermeticOrmus/vibe-engineer-skills) — Direct AI codegen well (hypothesis → scope → validate → reject working-but-wrong)
- [markdown-discipline-skills](https://github.com/HermeticOrmus/markdown-discipline-skills) — Strip AI-slop from markdown (no em dashes, no marketing fluff)
- [shell-safety-skills](https://github.com/HermeticOrmus/shell-safety-skills) — `set -euo pipefail` discipline + 15 failure-mode examples
- [commit-standard-skills](https://github.com/HermeticOrmus/commit-standard-skills) — Ormus Commit Standard v1.0 + commit-msg hook + commitlint
- [unwoke-skills](https://github.com/HermeticOrmus/unwoke-skills) — Strip AI theater (ten sins to eliminate, symmetric engagement)
- [python-conventions-skills](https://github.com/HermeticOrmus/python-conventions-skills) — Modern Python 3.11+ (types, pathlib, async, ruff, mypy, uv)
- [typescript-conventions-skills](https://github.com/HermeticOrmus/typescript-conventions-skills) — TypeScript strict mode, discriminated unions, Result types
- [hermetic-laws-skills](https://github.com/HermeticOrmus/hermetic-laws-skills) — Seven Hermetic Principles applied to engineering
- [riper-workflow-skills](https://github.com/HermeticOrmus/riper-workflow-skills) — Research / Innovate / Plan / Execute / Review systematic dev
- [six-day-cycle-skills](https://github.com/HermeticOrmus/six-day-cycle-skills) — Sustainable shipping cadence with mandatory rest
- [token-optimization-skills](https://github.com/HermeticOrmus/token-optimization-skills) — Claude Code token + context optimization
- [osint-skills](https://github.com/HermeticOrmus/osint-skills) — OSINT research methodology (multi-wave investigative spiral)
- [calcinate-skills](https://github.com/HermeticOrmus/calcinate-skills) — Stage 1 of the Magnum Opus (burn project bloat)
- [claude-md-overhaul-skills](https://github.com/HermeticOrmus/claude-md-overhaul-skills) — Audit CLAUDE.md and MEMORY.md against caps
- [session-handoff-skills](https://github.com/HermeticOrmus/session-handoff-skills) — Session handoff + pickup discipline
- [naming-skills](https://github.com/HermeticOrmus/naming-skills) — Product naming methodology (mine the brand's vocabulary)
- [magnum-opus-skills](https://github.com/HermeticOrmus/magnum-opus-skills) — Seven-stage alchemy applied to project transformation

### Template source

- [andrej-karpathy-skills](https://github.com/HermeticOrmus/andrej-karpathy-skills) — the canonical single-file CLAUDE.md pattern (fork of jiayuan_jy's original)

Star the family, not just one — that's how the suite stays coherent.

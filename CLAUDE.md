# pixel-art-pipeline

> Batch pixel art animation generator using PixelLab API

## Overview

This project follows the Gold Hat Philosophy: build what elevates, reject what degrades.

## Key Files

- `pixelart/client.py` -- PixelLab API wrapper
- `pixelart/assembler.py` -- Frame assembly (GIF/PNG)
- `pixelart/generator.py` -- Batch orchestration
- `pixelart/config.py` -- YAML config loader
- `pixelart/cli.py` -- CLI entry point

## Tech Stack

Python 3.10+, Pillow, Requests, PyYAML

## Development

### Commit Format
```
type(scope): description
```
Types: feat, fix, docs, refactor, test, chore

### Quality Standards
- Safety first: destructive operations require explicit confirmation
- Cross-platform: support Windows, macOS, and Linux where applicable
- Documentation: README stays current with implementation

## Philosophy

- **Empowerment over extraction** -- tools serve the user, not the other way around
- **Transparency** -- no hidden behavior, clear output, dry-run by default
- **Autonomy** -- users choose what to clean/change, never forced

---

*Hermetic Ormus | Gold Hat Technologist*

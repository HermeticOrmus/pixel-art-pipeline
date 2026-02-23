"""CLI entry point for pixel-art-pipeline."""

import argparse
import sys
from pathlib import Path

from . import __version__


def cmd_generate(args):
    """Generate animations from a config file."""
    from . import generator
    from .config import load_config

    config = load_config(args.config)
    errors = config.validate()
    if errors:
        print("Config validation errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Project: {config.name}")
    print(f"Output: {config.output_dir}")

    # Show balance before starting
    try:
        from .client import check_balance
        bal = check_balance()
        print(f"Balance: ${bal['credits_usd']:.2f}")
    except Exception as e:
        print(f"Balance check failed: {e}")

    total_cost = 0.0
    gen_type = args.type or "all"

    if gen_type in ("singles", "all"):
        total_cost += generator.generate_singles(config, args.target)

    if gen_type in ("emotes", "all"):
        total_cost += generator.generate_emotes(config, args.target)

    if gen_type in ("chains", "all"):
        total_cost += generator.generate_chains(config)

    if gen_type in ("journeys", "all"):
        total_cost += generator.generate_journeys(config, args.target)

    if gen_type in ("cycles", "all"):
        total_cost += generator.generate_cycles(config)

    print(f"\nTotal cost: ${total_cost:.2f}")

    try:
        from .client import check_balance
        bal = check_balance()
        print(f"Remaining balance: ${bal['credits_usd']:.2f}")
    except Exception:
        pass

    return 0


def cmd_assemble(args):
    """Assemble existing frames into GIFs."""
    from .config import load_config
    from .generator import assemble_all

    config = load_config(args.config)
    assemble_all(config)
    return 0


def cmd_balance(_args):
    """Check PixelLab API credit balance."""
    from .client import check_balance

    bal = check_balance()
    print(f"Credits: ${bal['credits_usd']:.2f} USD")
    print(f"Generations: {bal['generations_used']}/{bal['generations_total']}")
    return 0


def cmd_cost(args):
    """Estimate cost without generating anything."""
    from .config import load_config

    config = load_config(args.config)
    errors = config.validate()
    if errors:
        print("Config validation errors:")
        for e in errors:
            print(f"  - {e}")
        # Continue anyway — cost estimate doesn't need valid reference

    counts = config.count_animations()
    total = config.estimate_cost()

    print(f"Project: {config.name}")
    print("\nAnimation counts:")
    print(f"  Singles:  {counts['singles']:>4} animations  (~${counts['singles'] * 0.16:.2f})")
    print(f"  Emotes:   {counts['emotes']:>4} animations  (~${counts['emotes'] * 0.16:.2f})")
    print(f"  Chains:   {counts['chains']:>4} API calls    (~${counts['chains'] * 0.16:.2f})")
    print(f"  Journeys: {counts['journeys']:>4} API calls    (~${counts['journeys'] * 0.16:.2f})")
    print(f"  Cycles:   {counts['cycles']:>4} API calls    (~${counts['cycles'] * 0.16:.2f})")
    print(f"  {'-' * 40}")
    print(f"  Total:    {counts['total_api_calls']:>4} API calls")
    print(f"\nEstimated cost: ~${total:.2f}")
    return 0


def cmd_init(args):
    """Create a starter config and reference image."""
    from PIL import Image

    name = args.name or "my-project"
    project_dir = Path.cwd() / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple 64x64 gold circle as reference
    ref_path = project_dir / "reference.png"
    if not ref_path.exists():
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        pixels = img.load()
        cx, cy, r = 32, 32, 20
        for y in range(64):
            for x in range(64):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist <= r:
                    # Gold color with slight gradient
                    brightness = max(0, min(255, int(255 - dist * 3)))
                    pixels[x, y] = (255, 215, brightness // 2, 255)
        img.save(ref_path)
        print(f"Created reference image: {ref_path}")

    # Create starter config
    config_path = project_dir / "config.yaml"
    if not config_path.exists():
        config_path.write_text(
            f"""# {name} — Pixel Art Pipeline Config
# Docs: https://github.com/HermeticOrmus/pixel-art-pipeline

project:
  name: "{name}"
  reference: "reference.png"
  output_dir: "./output"
  frame_size: 64
  upscale_size: 512
  frame_duration_ms: 200

singles:
  flame:
    prompt: "golden circle transforms into a dancing flame"
  star:
    prompt: "golden circle transforms into a twinkling star with five points"
  heart:
    prompt: "golden circle transforms into a glowing heart shape"
  sword:
    prompt: "golden circle transforms into a pixel art sword standing upright"
  crown:
    prompt: "golden circle transforms into a royal crown with pointed tips"

emotes:
  flame:
    prompt: "a golden flame gently sways left and right, subtle idle animation"
  star:
    prompt: "a golden star twinkles, its points glowing brighter then dimmer"
  heart:
    prompt: "a golden heart pulses gently like a slow heartbeat"

chains:
  flame_to_heart:
    label: "Fire to Love"
    steps:
      - from: reference
        to: flame
        prompt: "golden circle transforms into a dancing flame"
      - from: flame
        to: heart
        prompt: "the flame softens and reshapes into a glowing heart"

cycles:
  cycle_flame:
    shape: flame
    forward_prompt: "golden circle transforms into a dancing flame"
    reverse_prompt: "flame dissolves back into a golden circle"
"""
        )
        print(f"Created config: {config_path}")

    print(f"\nProject initialized at: {project_dir}/")
    print("\nNext steps:")
    print(f"  1. Edit {config_path} to customize your animations")
    print(f"  2. Replace {ref_path} with your own 64x64 starting image")
    print("  3. export PIXELLAB_API_KEY=your-key-here")
    print(f"  4. pixelart cost --config {config_path}")
    print(f"  5. pixelart generate --config {config_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="pixelart",
        description="Batch pixel art animation generator using PixelLab API",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate animations from config")
    gen_parser.add_argument(
        "--config", "-c", default="config.yaml", help="Path to config.yaml (default: config.yaml)"
    )
    gen_parser.add_argument(
        "--type", "-t",
        choices=["singles", "emotes", "chains", "journeys", "cycles", "all"],
        help="Animation type to generate (default: all)",
    )
    gen_parser.add_argument(
        "--target", "-n", nargs="*",
        help="Specific animation names to generate (for singles/emotes/journeys)",
    )

    # assemble
    asm_parser = subparsers.add_parser("assemble", help="Assemble existing frames into GIFs")
    asm_parser.add_argument(
        "--config", "-c", default="config.yaml", help="Path to config.yaml"
    )

    # balance
    subparsers.add_parser("balance", help="Check PixelLab API credit balance")

    # cost
    cost_parser = subparsers.add_parser("cost", help="Estimate cost without generating")
    cost_parser.add_argument(
        "--config", "-c", default="config.yaml", help="Path to config.yaml"
    )

    # init
    init_parser = subparsers.add_parser("init", help="Create a starter project")
    init_parser.add_argument(
        "--name", "-n", default=None, help="Project name (default: my-project)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "generate": cmd_generate,
        "assemble": cmd_assemble,
        "balance": cmd_balance,
        "cost": cmd_cost,
        "init": cmd_init,
    }

    try:
        return commands[args.command](args)
    except KeyboardInterrupt:
        print("\nAborted.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

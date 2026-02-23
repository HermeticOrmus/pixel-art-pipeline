"""Batch animation generation orchestrator."""

import base64
import tempfile
import time
from pathlib import Path

from .assembler import frames_to_gif, save_frames, save_frames_offset
from .client import generate_animation
from .config import PipelineConfig


def _has_frames(directory: Path, min_count: int = 16) -> bool:
    """Check if a directory already has enough frames (skip-if-exists)."""
    if not directory.exists():
        return False
    return len(list(directory.glob("frame_*.png"))) >= min_count


def _assemble_animation(config: PipelineConfig, frame_dir: Path, name: str):
    """Assemble GIF + static fallback for a completed animation."""
    gif_path = frame_dir.parent / f"{name}.gif"
    frames_to_gif(frame_dir, gif_path, config.upscale_size, config.frame_duration_ms)
    if gif_path.exists():
        size_kb = gif_path.stat().st_size / 1024
        print(f"    GIF: {gif_path.name} ({size_kb:.0f}KB)")

    from .assembler import create_static_fallback

    static_path = config.static_dir / f"{name}.png"
    create_static_fallback(frame_dir, static_path, config.upscale_size)


def generate_singles(
    config: PipelineConfig, targets: list[str] | None = None
) -> float:
    """Generate single reference-to-shape transforms.

    Returns total cost in USD.
    """
    items = config.singles
    if targets:
        items = {k: v for k, v in items.items() if k in targets}

    if not items:
        print("No singles to generate.")
        return 0.0

    print(f"\n{'=' * 60}")
    print(f"GENERATING {len(items)} SINGLE TRANSFORMS")
    print(f"{'=' * 60}")
    print(f"Estimated cost: ~${len(items) * 0.16:.2f}")
    print(f"Reference: {config.reference}")
    print()

    total_cost = 0.0
    for name, entry in items.items():
        frame_dir = config.singles_dir / name

        if _has_frames(frame_dir):
            existing = len(list(frame_dir.glob("frame_*.png")))
            print(f"  SKIP {name} (already has {existing} frames)")
            continue

        print(f"  Generating: {name}")
        try:
            frames, cost = generate_animation(
                config.reference,
                entry["prompt"],
                width=config.frame_size,
                height=config.frame_size,
            )
            saved = save_frames(frames, frame_dir)
            total_cost += cost
            print(f"    Saved {len(saved)} frames (${cost:.4f})")
            _assemble_animation(config, frame_dir, name)
            time.sleep(1)
        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"\nSingles complete. Cost: ${total_cost:.2f}")
    return total_cost


def generate_emotes(
    config: PipelineConfig, targets: list[str] | None = None
) -> float:
    """Generate emote animations using the last frame of each single as reference.

    Emote frames are saved as frame_16 through frame_31 in the singles directory.

    Returns total cost in USD.
    """
    items = config.emotes
    if targets:
        items = {k: v for k, v in items.items() if k in targets}

    if not items:
        print("No emotes to generate.")
        return 0.0

    print(f"\n{'=' * 60}")
    print(f"GENERATING EMOTES FOR {len(items)} SHAPES")
    print(f"{'=' * 60}")
    print(f"Estimated cost: ~${len(items) * 0.16:.2f}")
    print()

    total_cost = 0.0
    for name, entry in items.items():
        frame_dir = config.singles_dir / name
        ref_frame = frame_dir / "frame_15.png"

        if not ref_frame.exists():
            print(f"  SKIP {name} (no frame_15.png — generate singles first)")
            continue

        if (frame_dir / "frame_16.png").exists():
            print(f"  SKIP {name} (emote frames already exist)")
            continue

        print(f"  Emote: {name}")
        try:
            frames, cost = generate_animation(
                ref_frame,
                entry["prompt"],
                width=config.frame_size,
                height=config.frame_size,
            )
            save_frames_offset(frames, frame_dir, offset=16)
            total_cost += cost
            print(f"    Saved {len(frames)} emote frames (${cost:.4f})")

            # Reassemble GIF with all frames (transform + emote)
            _assemble_animation(config, frame_dir, name)
            time.sleep(1)
        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"\nEmotes complete. Cost: ${total_cost:.2f}")
    return total_cost


def generate_chains(config: PipelineConfig) -> float:
    """Generate 2-step chain sequences.

    Returns total cost in USD.
    """
    if not config.chains:
        print("No chains to generate.")
        return 0.0

    total_steps = sum(len(c.get("steps", [])) for c in config.chains.values())
    print(f"\n{'=' * 60}")
    print(f"GENERATING {len(config.chains)} CHAINS ({total_steps} steps)")
    print(f"{'=' * 60}")
    print(f"Estimated cost: ~${total_steps * 0.16:.2f}")
    print()

    total_cost = 0.0
    for chain_name, entry in config.chains.items():
        steps = entry.get("steps", [])
        chain_dir = config.chains_dir / chain_name
        expected_frames = len(steps) * 16

        if _has_frames(chain_dir, expected_frames):
            print(f"  SKIP {chain_name} (already complete)")
            continue

        label = entry.get("label", chain_name)
        print(f"  Chain: {label}")
        chain_dir.mkdir(parents=True, exist_ok=True)

        all_frames = []
        for step_idx, step in enumerate(steps):
            ref = _resolve_step_reference(config, step, all_frames)
            from_s, to_s = step.get("from", "?"), step.get("to", "?")
            print(f"    Step {step_idx + 1}/{len(steps)}: {from_s} -> {to_s}")
            try:
                frames, cost = generate_animation(
                    ref,
                    step["prompt"],
                    width=config.frame_size,
                    height=config.frame_size,
                )
                all_frames.extend(frames)
                total_cost += cost
                print(f"      ${cost:.4f}")
                time.sleep(1)
            except Exception as e:
                print(f"      ERROR: {e}")
                break

        if all_frames:
            saved = save_frames(all_frames, chain_dir)
            print(f"    Saved {len(saved)} total frames")
            _assemble_animation(config, chain_dir, chain_name)

    print(f"\nChains complete. Cost: ${total_cost:.2f}")
    return total_cost


def generate_journeys(
    config: PipelineConfig, targets: list[str] | None = None
) -> float:
    """Generate multi-step journey sequences (3-5 steps).

    Returns total cost in USD.
    """
    items = config.journeys
    if targets:
        items = {k: v for k, v in items.items() if k in targets}

    if not items:
        print("No journeys to generate.")
        return 0.0

    total_steps = sum(len(j.get("steps", [])) for j in items.values())
    print(f"\n{'=' * 60}")
    print(f"GENERATING {len(items)} JOURNEYS ({total_steps} steps)")
    print(f"{'=' * 60}")
    print(f"Estimated cost: ~${total_steps * 0.16:.2f}")
    print()

    total_cost = 0.0
    for journey_name, entry in items.items():
        steps = entry.get("steps", [])
        journey_dir = config.journeys_dir / journey_name
        expected_frames = len(steps) * 16

        if _has_frames(journey_dir, expected_frames):
            print(f"  SKIP {journey_name} (already complete)")
            continue

        label = entry.get("label", journey_name)
        print(f"  Journey: {label} ({len(steps)} steps)")
        journey_dir.mkdir(parents=True, exist_ok=True)

        all_frames = []
        for step_idx, step in enumerate(steps):
            ref = _resolve_step_reference(config, step, all_frames)
            from_s, to_s = step.get("from", "?"), step.get("to", "?")
            print(f"    Step {step_idx + 1}/{len(steps)}: {from_s} -> {to_s}")
            try:
                frames, cost = generate_animation(
                    ref,
                    step["prompt"],
                    width=config.frame_size,
                    height=config.frame_size,
                )
                all_frames.extend(frames)
                total_cost += cost
                print(f"      ${cost:.4f}")
                time.sleep(1)
            except Exception as e:
                print(f"      ERROR: {e}")
                break

        if all_frames:
            saved = save_frames(all_frames, journey_dir)
            print(f"    Saved {len(saved)} total frames")
            _assemble_animation(config, journey_dir, journey_name)

    print(f"\nJourneys complete. Cost: ${total_cost:.2f}")
    return total_cost


def generate_cycles(config: PipelineConfig) -> float:
    """Generate full cycle animations (reference -> shape -> reference, loops).

    Reuses existing forward singles if available.

    Returns total cost in USD.
    """
    if not config.cycles:
        print("No cycles to generate.")
        return 0.0

    print(f"\n{'=' * 60}")
    print(f"GENERATING {len(config.cycles)} FULL CYCLES")
    print(f"{'=' * 60}")
    print(f"Estimated cost: ~${len(config.cycles) * 0.16:.2f} (reusing forward singles)")
    print()

    total_cost = 0.0
    for cycle_name, entry in config.cycles.items():
        cycle_dir = config.cycles_dir / cycle_name

        if _has_frames(cycle_dir, 32):
            print(f"  SKIP {cycle_name} (already complete)")
            continue

        shape = entry["shape"]
        forward_dir = config.singles_dir / shape
        forward_frames = sorted(forward_dir.glob("frame_*.png")) if forward_dir.exists() else []

        print(f"  Cycle: {cycle_name}")

        # Generate forward if not already in singles
        if not forward_frames:
            print(f"    Generating forward: {shape}")
            try:
                frames, cost = generate_animation(
                    config.reference,
                    entry["forward_prompt"],
                    width=config.frame_size,
                    height=config.frame_size,
                )
                save_frames(frames, forward_dir)
                forward_frames = sorted(forward_dir.glob("frame_*.png"))
                total_cost += cost
                time.sleep(1)
            except Exception as e:
                print(f"    ERROR generating forward: {e}")
                continue

        # Generate reverse using last forward frame as reference
        last_frame = forward_frames[-1]
        print(f"    Generating reverse: {shape} -> reference")
        try:
            reverse_frames, cost = generate_animation(
                last_frame,
                entry["reverse_prompt"],
                width=config.frame_size,
                height=config.frame_size,
            )
            total_cost += cost
            time.sleep(1)
        except Exception as e:
            print(f"    ERROR generating reverse: {e}")
            continue

        # Combine: read forward frame bytes + reverse frame data
        all_frames = []
        for fp in forward_frames:
            with open(fp, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            all_frames.append({"type": "base64", "base64": b64, "format": "png"})
        all_frames.extend(reverse_frames)

        saved = save_frames(all_frames, cycle_dir)
        print(f"    Saved {len(saved)} total frames (forward + reverse)")
        _assemble_animation(config, cycle_dir, cycle_name)

    print(f"\nCycles complete. Cost: ${total_cost:.2f}")
    return total_cost


def assemble_all(config: PipelineConfig):
    """Assemble GIFs and static fallbacks for all existing frame directories."""
    print(f"\n{'=' * 60}")
    print("ASSEMBLING GIFs + STATIC FALLBACKS")
    print(f"{'=' * 60}")

    count = 0
    for type_dir in [config.singles_dir, config.emotes_dir, config.chains_dir,
                     config.journeys_dir, config.cycles_dir]:
        if not type_dir.exists():
            continue
        for frame_dir in sorted(type_dir.iterdir()):
            if not frame_dir.is_dir():
                continue
            frames = sorted(frame_dir.glob("frame_*.png"))
            if not frames:
                continue
            _assemble_animation(config, frame_dir, frame_dir.name)
            count += 1

    print(f"\nAssembled {count} animations.")


def _resolve_step_reference(
    config: PipelineConfig, step: dict, previous_frames: list[dict]
) -> Path:
    """Resolve the reference image for a chain/journey step.

    Priority:
    1. 'from' == first step or 'liquid' (or similar) -> use project reference
    2. 'from' matches a singles name -> use that single's frame_15
    3. Fall back to last frame from previous generation in this chain
    4. Fall back to project reference
    """
    from_shape = step.get("from", "")

    # If first step or explicitly referencing the base
    if not from_shape or from_shape in ("liquid", "reference", "base"):
        return config.reference

    # Try to find the shape in singles output
    shape_dir = config.singles_dir / from_shape
    ref = shape_dir / "frame_15.png"
    if ref.exists():
        return ref

    # Fall back to last frame from previous steps in this sequence
    if previous_frames:
        tmp = Path(tempfile.mktemp(suffix=".png"))
        with open(tmp, "wb") as f:
            f.write(base64.b64decode(previous_frames[-1]["base64"]))
        return tmp

    # Ultimate fallback
    return config.reference

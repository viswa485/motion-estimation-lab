"""Generate a deterministic synthetic video for the optional FFmpeg experiment.

The generated source is encoded with libx264, then used as the reference input
when measuring a separate libx265 CRF sweep. This does not test the custom C++
motion-search algorithm inside either encoder.
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path

from .data import make_reference, translate_frame, write_pgm


def _require_encoder(ffmpeg: str, encoder: str) -> None:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Could not query FFmpeg encoders: {detail}")

    # Encoder names are the second whitespace-delimited column in FFmpeg output.
    available = any(
        len(parts := line.split()) >= 2 and parts[1] == encoder
        for line in result.stdout.splitlines()
    )
    if not available:
        raise RuntimeError(
            f"FFmpeg encoder '{encoder}' is unavailable. Install an FFmpeg build "
            f"with {encoder} support and verify it with: ffmpeg -hide_banner -encoders"
        )


def generate_video(
    output_path: Path,
    frames_dir: Path,
    width: int = 160,
    height: int = 96,
    fps: int = 16,
    frame_count: int = 32,
    seed: int = 20261025,
) -> Path:
    """Create a moving synthetic clip and encode it with FFmpeg/libx264.

    Frames are first saved as portable grayscale PGM files, so they can be
    inspected independently and regenerated from the same seed and parameters.
    The output has frame_count / fps seconds of video (2 seconds by default).
    """
    if width < 16 or height < 16:
        raise ValueError("width and height must both be at least 16 pixels")
    if width % 2 or height % 2:
        raise ValueError("width and height must be even for yuv420p output")
    if fps <= 0:
        raise ValueError("fps must be positive")
    if frame_count < 2:
        raise ValueError("frame_count must be at least 2")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg was not found. Install FFmpeg before generating the demo video.")
    _require_encoder(ffmpeg, "libx264")

    output_path = Path(output_path).expanduser().resolve()
    frames_dir = Path(frames_dir).expanduser().resolve()
    if output_path == frames_dir or frames_dir in output_path.parents:
        raise ValueError("The video output path must not be inside the generated frames directory")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    reference = make_reference(width=width, height=height, seed=seed)
    for index in range(frame_count):
        phase = 2.0 * math.pi * index / frame_count
        dx = int(round(4.0 * math.sin(phase)))
        dy = int(round(2.0 * math.cos(phase)))
        frame_path = frames_dir / f"frame_{index:04d}.pgm"
        write_pgm(frame_path, translate_frame(reference, dx=dx, dy=dy))

    frame_pattern = frames_dir / "frame_%04d.pgm"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-framerate",
        str(fps),
        "-start_number",
        "0",
        "-i",
        str(frame_pattern),
        "-frames:v",
        str(frame_count),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0 or not output_path.is_file() or output_path.stat().st_size == 0:
        detail = completed.stderr.strip() or "FFmpeg did not create a non-empty video."
        raise RuntimeError(f"Could not generate demo video: {detail}")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/demo_source.mp4"))
    parser.add_argument("--frames-dir", type=Path, default=Path("data/demo_video_frames"))
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=96)
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument("--frames", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20261025)
    args = parser.parse_args()

    video = generate_video(
        args.output,
        args.frames_dir,
        width=args.width,
        height=args.height,
        fps=args.fps,
        frame_count=args.frames,
        seed=args.seed,
    )
    print(
        f"Generated {video} ({args.frames} frames at {args.fps} fps; "
        f"{args.frames / args.fps:.2f} seconds)"
    )


if __name__ == "__main__":
    main()

"""Generate a small deterministic grayscale frame pair for the demo."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np

def _draw_rectangle(frame: np.ndarray, x0: int, y0: int, x1: int, y1: int, value: int) -> None:
    frame[max(0, y0):min(frame.shape[0], y1), max(0, x0):min(frame.shape[1], x1)] = value

def make_reference(width: int = 192, height: int = 128, seed: int = 20261025) -> np.ndarray:
    """Create a deterministic textured scene with edges and flat regions."""
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:height, 0:width]
    base = 68 + 0.45 * xx + 0.28 * yy + 18 * np.sin(xx / 9.0) + 10 * np.cos(yy / 7.0)
    texture = rng.normal(0.0, 8.0, size=(height, width))
    frame = np.clip(base + texture, 0, 255).astype(np.uint8)
    _draw_rectangle(frame, 18, 17, 62, 48, 220)
    _draw_rectangle(frame, 74, 28, 108, 90, 28)
    _draw_rectangle(frame, 128, 16, 173, 56, 176)
    _draw_rectangle(frame, 25, 78, 54, 112, 115)
    _draw_rectangle(frame, 132, 78, 182, 111, 238)
    frame[60:64, 10:180] = 245
    frame[12:115:7, 93:96] = 8
    return frame

def translate_frame(reference: np.ndarray, dx: int = 3, dy: int = -2) -> np.ndarray:
    """Construct current(x,y)=reference(x+dx,y+dy), clamping at image borders."""
    height, width = reference.shape
    ys = np.clip(np.arange(height) + dy, 0, height - 1)
    xs = np.clip(np.arange(width) + dx, 0, width - 1)
    return reference[np.ix_(ys, xs)].copy()

def write_pgm(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if frame.ndim != 2 or frame.dtype != np.uint8 or frame.shape[0] <= 0 or frame.shape[1] <= 0:
        raise ValueError("Expected a non-empty 2D uint8 grayscale frame")
    height, width = frame.shape
    with path.open("wb") as handle:
        handle.write(f"P5\n{width} {height}\n255\n".encode("ascii"))
        handle.write(frame.tobytes(order="C"))

def generate_pair(output_dir: Path, width: int = 192, height: int = 128,
                  dx: int = 3, dy: int = -2, seed: int = 20261025) -> tuple[Path, Path]:
    reference = make_reference(width=width, height=height, seed=seed)
    current = translate_frame(reference, dx=dx, dy=dy)
    reference_path = output_dir / "reference.pgm"
    current_path = output_dir / "current.pgm"
    write_pgm(reference_path, reference)
    write_pgm(current_path, current)
    return reference_path, current_path

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/demo"))
    parser.add_argument("--width", type=int, default=192)
    parser.add_argument("--height", type=int, default=128)
    parser.add_argument("--dx", type=int, default=3)
    parser.add_argument("--dy", type=int, default=-2)
    parser.add_argument("--seed", type=int, default=20261025)
    args = parser.parse_args()
    reference, current = generate_pair(args.output_dir, args.width, args.height, args.dx, args.dy, args.seed)
    print(f"Generated {reference} and {current} (known translation dx={args.dx}, dy={args.dy})")

if __name__ == "__main__":
    main()

"""Python orchestration layer with repeated runs and median runtime summaries."""
from __future__ import annotations
import argparse
import csv
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_FIELDS = ["algorithm", "width", "height", "block_size", "search_range", "blocks",
              "total_candidates", "avg_candidates_per_block", "avg_sad_per_pixel",
              "mc_psnr_db", "elapsed_ms", "blocks_per_second"]
SUMMARY_FIELDS = RAW_FIELDS + ["repeats", "elapsed_ms_min", "elapsed_ms_max", "elapsed_ms_stddev"]

def ensure_binary(build: bool = False) -> Path:
    configured = ROOT / "build" / "me_bench"
    if configured.exists():
        return configured
    if not build:
        raise FileNotFoundError(f"Benchmark binary not found at {configured}. Build it with: cmake -S . -B build && cmake --build build --parallel")
    if shutil.which("cmake") is None:
        raise RuntimeError("CMake was not found. Install CMake and a C++17 compiler first.")
    subprocess.run(["cmake", "-S", str(ROOT), "-B", str(ROOT / "build")], check=True)
    subprocess.run(["cmake", "--build", str(ROOT / "build"), "--parallel"], check=True)
    if not configured.exists():
        raise FileNotFoundError(f"CMake finished but {configured} was not created")
    return configured

def run(reference: Path, current: Path, output: Path, block_size: int = 16,
        search_range: int = 8, algorithm: str = "all", build: bool = False,
        repeats: int = 5) -> Path:
    if repeats < 1 or repeats > 50:
        raise ValueError("repeats must be between 1 and 50")
    reference, current, output = reference.resolve(), current.resolve(), output.resolve()
    raw_path = output.with_name(f"{output.stem}_runs.csv")
    if output in {reference, current} or raw_path in {reference, current}:
        raise ValueError("Output paths must not overwrite input frame files")
    if not reference.is_file() or not current.is_file():
        raise FileNotFoundError("Both reference and current PGM paths must exist")
    binary = ensure_binary(build=build)
    output.parent.mkdir(parents=True, exist_ok=True)
    collected: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="me-lab-") as temporary_dir:
        for repeat_index in range(1, repeats + 1):
            raw_output = Path(temporary_dir) / f"run_{repeat_index}.csv"
            command = [str(binary), "--reference", str(reference), "--current", str(current),
                       "--block-size", str(block_size), "--search-range", str(search_range),
                       "--algorithm", algorithm, "--output", str(raw_output)]
            completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
            with raw_output.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    collected.append({"run": str(repeat_index), **row})
            if completed.stderr.strip():
                print(completed.stderr.strip())
    with raw_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run", *RAW_FIELDS])
        writer.writeheader()
        writer.writerows(collected)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in collected:
        grouped.setdefault(row["algorithm"], []).append(row)
    summaries: list[dict[str, str | int | float]] = []
    for name, rows in grouped.items():
        times = [float(row["elapsed_ms"]) for row in rows]
        median_time = statistics.median(times)
        summary: dict[str, str | int | float] = {field: rows[0][field] for field in RAW_FIELDS}
        summary["elapsed_ms"] = median_time
        blocks = float(rows[0]["blocks"])
        summary["blocks_per_second"] = blocks / (median_time / 1000.0) if median_time > 0 else 0.0
        summary["repeats"] = len(rows)
        summary["elapsed_ms_min"] = min(times)
        summary["elapsed_ms_max"] = max(times)
        summary["elapsed_ms_stddev"] = statistics.pstdev(times) if len(times) > 1 else 0.0
        summaries.append(summary)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summaries)
    print(f"Recorded {len(collected)} run rows in {raw_path}")
    print(f"Median-runtime summary written to {output}")
    return output

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=ROOT / "data/demo/reference.pgm")
    parser.add_argument("--current", type=Path, default=ROOT / "data/demo/current.pgm")
    parser.add_argument("--output", type=Path, default=ROOT / "results/benchmark.csv")
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--search-range", type=int, default=8)
    parser.add_argument("--algorithm", default="all", choices=["all", "full_search", "three_step", "diamond", "predictive_diamond"])
    parser.add_argument("--repeats", type=int, default=5, help="Runs per algorithm; summary uses median runtime (1..50)")
    parser.add_argument("--build", action="store_true", help="Build the C++ binary if not present")
    args = parser.parse_args()
    path = run(args.reference, args.current, args.output, args.block_size, args.search_range, args.algorithm, args.build, args.repeats)
    print(f"Benchmark summary CSV: {path}")

if __name__ == "__main__":
    main()

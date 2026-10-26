"""Measure an external FFmpeg encoder's bitrate/PSNR/runtime across CRF points."""
from __future__ import annotations
import argparse
import csv
import re
import shutil
import statistics
import subprocess
import time
from pathlib import Path

def ffprobe_duration(ffprobe: str, video_path: Path) -> float:
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
                            check=True, capture_output=True, text=True)
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Could not determine duration of {video_path}") from exc
    if duration <= 0:
        raise RuntimeError(f"Invalid duration reported for {video_path}")
    return duration

def measure_psnr(ffmpeg: str, encoded: Path, source: Path) -> float:
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(encoded), "-i", str(source),
                             "-lavfi", "psnr", "-f", "null", "-"],
                            check=False, capture_output=True, text=True)
    output = result.stderr + "\n" + result.stdout
    if result.returncode != 0:
        raise RuntimeError("FFmpeg PSNR measurement failed.\n" + output[-2000:])
    matches = re.findall(r"average:([0-9]+(?:\.[0-9]+)?|inf)", output)
    if not matches:
        raise RuntimeError("Could not parse FFmpeg PSNR summary. Confirm source/output dimensions and frame rates.\n" + output[-2000:])
    return float(matches[-1]) if matches[-1] != "inf" else float("inf")

def run_matrix(input_video: Path, output_csv: Path, crfs: list[int], preset: str = "medium",
               encoder: str = "libx265", work_dir: Path | None = None, repeats: int = 3) -> Path:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        raise RuntimeError("Both ffmpeg and ffprobe must be installed")

    encoder_result = subprocess.run(
        [ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    if encoder_result.returncode != 0:
        detail = encoder_result.stderr.strip() or encoder_result.stdout.strip()
        raise RuntimeError(f"Could not query FFmpeg encoders: {detail}")
    if not any(
        len(fields := line.split()) >= 2 and fields[1] == encoder
        for line in encoder_result.stdout.splitlines()
    ):
        raise RuntimeError(
            f"FFmpeg encoder '{encoder}' is unavailable. Check the encoder name "
            "and install an FFmpeg build that includes it."
        )

    input_video = input_video.resolve()
    if not input_video.is_file():
        raise FileNotFoundError(f"Input video does not exist: {input_video}")
    if not crfs:
        raise ValueError("Provide at least one CRF value")
    if repeats < 1 or repeats > 20:
        raise ValueError("repeats must be between 1 and 20")
    if any(crf < 0 or crf > 51 for crf in crfs):
        raise ValueError("CRF values must be between 0 and 51")
    output_csv = output_csv.resolve()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    run_dir = (work_dir or output_csv.parent / "encoder_runs").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    duration = ffprobe_duration(ffprobe, input_video)
    rows: list[dict[str, object]] = []
    for crf in crfs:
        encoded = run_dir / f"{input_video.stem}_{encoder}_crf{crf}.mkv"
        elapsed_runs: list[float] = []
        size_bytes = 0
        for repeat_index in range(1, repeats + 1):
            command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(input_video),
                       "-an", "-c:v", encoder, "-preset", preset, "-crf", str(crf), str(encoded)]
            start = time.perf_counter()
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            elapsed_runs.append(time.perf_counter() - start)
            if result.returncode != 0 or not encoded.exists():
                raise RuntimeError(f"Encoding failed for {encoder} CRF {crf}. Is this encoder available in your FFmpeg build?\n" + result.stderr[-2000:])
            size_bytes = encoded.stat().st_size
        psnr = measure_psnr(ffmpeg, encoded, input_video)
        median_elapsed = statistics.median(elapsed_runs)
        rows.append({
            "input": input_video.name, "encoder": encoder, "preset": preset, "crf": crf,
            "duration_seconds": duration, "size_bytes": size_bytes,
            "bitrate_kbps": size_bytes * 8.0 / duration / 1000.0,
            "decoded_video_psnr_db": psnr, "encode_seconds": median_elapsed,
            "encode_repeats": repeats, "encode_seconds_min": min(elapsed_runs),
            "encode_seconds_max": max(elapsed_runs),
            "encode_seconds_stddev": statistics.pstdev(elapsed_runs) if len(elapsed_runs) > 1 else 0.0,
            "output_file": str(encoded.relative_to(output_csv.parent)) if encoded.is_relative_to(output_csv.parent) else str(encoded),
        })
        print(f"{encoder} CRF {crf}: {rows[-1]['bitrate_kbps']:.2f} kb/s, PSNR {psnr:.3f} dB, median {median_elapsed:.2f}s ({repeats} runs)")
    fields = ["input", "encoder", "preset", "crf", "duration_seconds", "size_bytes", "bitrate_kbps",
              "decoded_video_psnr_db", "encode_seconds", "encode_repeats", "encode_seconds_min",
              "encode_seconds_max", "encode_seconds_stddev", "output_file"]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return output_csv

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Input video; output is compared to this decoded source")
    parser.add_argument("--output", type=Path, default=Path("results/encoder_rd.csv"))
    parser.add_argument("--crf", type=int, nargs="+", default=[22, 27, 32, 37])
    parser.add_argument("--preset", default="medium")
    parser.add_argument("--encoder", default="libx265", help="FFmpeg encoder name; default is HEVC libx265")
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--repeats", type=int, default=3, help="Encode-time repetitions per CRF (1..20)")
    args = parser.parse_args()
    path = run_matrix(args.input, args.output, args.crf, args.preset, args.encoder, args.work_dir, args.repeats)
    print(f"Rate-distortion matrix written to {path}")

if __name__ == "__main__":
    main()

from __future__ import annotations
import csv
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "build" / "me_bench"

@pytest.mark.skipif(not BINARY.exists(), reason="C++ benchmark must be built first")
def test_cli_outputs_all_algorithms(tmp_path: Path) -> None:
    reference, current = ROOT / "data/demo/reference.pgm", ROOT / "data/demo/current.pgm"
    output = tmp_path / "benchmark.csv"
    subprocess.run([str(BINARY), "--reference", str(reference), "--current", str(current),
                   "--block-size", "16", "--search-range", "8", "--algorithm", "all",
                   "--output", str(output)], check=True, cwd=ROOT, capture_output=True, text=True)
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["algorithm"] for row in rows} == {"full_search", "three_step", "diamond", "predictive_diamond"}
    assert all(float(row["avg_candidates_per_block"]) > 0 for row in rows)
    assert all(float(row["avg_sad_per_pixel"]) >= 0 for row in rows)

def test_demo_generator_is_reproducible(tmp_path: Path) -> None:
    from codec_lab.data import generate_pair
    ref1, cur1 = generate_pair(tmp_path / "first")
    ref2, cur2 = generate_pair(tmp_path / "second")
    assert ref1.read_bytes() == ref2.read_bytes()
    assert cur1.read_bytes() == cur2.read_bytes()

@pytest.mark.skipif(not BINARY.exists(), reason="C++ benchmark must be built first")
def test_local_api_executes_benchmark_and_rejects_path_escape() -> None:
    from fastapi.testclient import TestClient
    from codec_lab.api import app
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["binary_built"] is True
    response = client.post("/benchmarks", json={"reference":"data/demo/reference.pgm",
        "current":"data/demo/current.pgm","block_size":16,"search_range":8,"algorithm":"predictive_diamond"})
    assert response.status_code == 200, response.text
    assert response.json()["rows"][0]["algorithm"] == "predictive_diamond"
    escaped = client.post("/benchmarks", json={"reference":"../../etc/passwd",
        "current":"data/demo/current.pgm","block_size":16,"search_range":8,"algorithm":"all"})
    assert escaped.status_code == 400

@pytest.mark.skipif(not BINARY.exists(), reason="C++ benchmark must be built first")
def test_python_runner_writes_median_and_raw_runs(tmp_path: Path) -> None:
    from codec_lab.runner import run
    output = tmp_path / "summary.csv"
    run(ROOT / "data/demo/reference.pgm", ROOT / "data/demo/current.pgm", output,
        block_size=16, search_range=8, algorithm="predictive_diamond", repeats=2)
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["algorithm"] == "predictive_diamond" and rows[0]["repeats"] == "2"
    assert (tmp_path / "summary_runs.csv").is_file()

def _ffmpeg_has_encoder(encoder: str) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    result = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True)
    if result.returncode != 0:
        return False
    return any(
        len(fields := line.split()) >= 2 and fields[1] == encoder
        for line in result.stdout.splitlines()
    )


def _ffmpeg_has_libx265() -> bool:
    return _ffmpeg_has_encoder("libx265")


@pytest.mark.skipif(not _ffmpeg_has_encoder("libx264"), reason="FFmpeg libx264 encoder is unavailable")
def test_demo_video_generator_creates_expected_clip(tmp_path: Path) -> None:
    from codec_lab.demo_video import generate_video

    video = generate_video(tmp_path / "demo_source.mp4", tmp_path / "frames")
    assert video.is_file() and video.stat().st_size > 0
    frames = sorted((tmp_path / "frames").glob("frame_*.pgm"))
    assert len(frames) == 32
    assert frames[0].read_bytes().startswith(b"P5")


@pytest.mark.skipif(not _ffmpeg_has_libx265(), reason="Optional FFmpeg libx265 encoder is unavailable")
def test_optional_encoder_matrix_records_rate_distortion(tmp_path: Path) -> None:
    from codec_lab.encoder_matrix import run_matrix
    from codec_lab.demo_video import generate_video
    source = generate_video(tmp_path / "demo_source.mp4", tmp_path / "frames")
    output = run_matrix(source, tmp_path / "encoder_rd.csv", [37], preset="ultrafast",
                        encoder="libx265", work_dir=tmp_path / "encoded", repeats=2)
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["bitrate_kbps"]) > 0 and float(rows[0]["decoded_video_psnr_db"]) > 0
    assert rows[0]["encode_repeats"] == "2"

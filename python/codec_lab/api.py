"""Optional FastAPI service for running controlled local benchmark jobs."""
from __future__ import annotations
import csv
import io
import subprocess
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / "build" / "me_bench"
app = FastAPI(title="Motion Estimation Lab API", version="0.1.0")

class BenchmarkRequest(BaseModel):
    reference: str = "data/demo/reference.pgm"
    current: str = "data/demo/current.pgm"
    block_size: int = Field(default=16, ge=1, le=128)
    search_range: int = Field(default=8, ge=0, le=64)
    algorithm: Literal["all", "full_search", "three_step", "diamond", "predictive_diamond"] = "all"

def _safe_project_file(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Input paths must remain inside the repository") from exc
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"Input file not found: {relative_path}")
    return candidate

@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "binary_built": BINARY.is_file()}

@app.post("/benchmarks")
def run_benchmark(request: BenchmarkRequest) -> dict[str, object]:
    if not BINARY.is_file():
        raise HTTPException(status_code=503, detail="Build the C++ benchmark first: cmake -S . -B build && cmake --build build")
    reference = _safe_project_file(request.reference)
    current = _safe_project_file(request.current)
    command = [str(BINARY), "--reference", str(reference), "--current", str(current),
               "--block-size", str(request.block_size), "--search-range", str(request.search_range),
               "--algorithm", request.algorithm, "--output", str(ROOT / "results/api_benchmark.csv")]
    try:
        completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=408, detail="Benchmark exceeded the 120-second request limit") from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=422, detail=exc.stderr.strip() or "Benchmark failed") from exc
    csv_text = (ROOT / "results/api_benchmark.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    return {"rows": rows, "stdout": completed.stdout.strip(), "scope_note": "Motion-compensation PSNR is not encoded-video PSNR or BD-rate."}

# Motion Estimation Lab

**A reproducible C++ / Python research prototype for comparing block-matching motion-search algorithms.**

The project isolates a performance-critical decision in inter-frame video coding: where should an encoder search in the reference frame for the best match to a current block? It compares exhaustive full search with three faster strategies, measuring candidate evaluations, residual error, motion-compensated PSNR, and wall-clock runtime.

> **Research scope:** This repository implements a standalone motion-estimation experiment. It is not an HEVC/VVC-compliant encoder, and the search code is not yet patched into HM, VTM, or VVenC. Local SAD and motion-compensation metrics are not encoded bitrate, encoded-video PSNR, BD-rate, or a claim of end-to-end compression gain.

## Features

- C++17 block matching with full search, three-step search, diamond search, and predictor-guided diamond search.
- Deterministic synthetic frame-pair generation and PGM input.
- Python orchestration and repeatable CSV benchmark records.
- Pandas/Matplotlib reports for candidate count, quality, and runtime.
- Optional FastAPI benchmark endpoint.
- Optional FFmpeg/libx265 CRF matrix for encoded bitrate, decoded-video PSNR, and encoding-time measurement.
- CMake build, C++/Python tests, and GitHub Actions CI.

## Quick start (macOS/Linux)

Requirements: Python 3.10+, a C++17 compiler, CMake, and pip.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
./scripts/run_demo.sh
pytest -q
```

The demo script builds the C++ code, runs tests and benchmarks, and writes CSVs and plots to `results/`.

### Run individual steps

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python -m codec_lab.data --output-dir data/demo
python -m codec_lab.runner --reference data/demo/reference.pgm --current data/demo/current.pgm --output results/benchmark.csv --block-size 16 --search-range 8 --algorithm all --repeats 5
python -m codec_lab.report results/benchmark.csv --output-dir results/report
```

### Optional real encoder experiment

Install FFmpeg with `libx265` support, then run:

```bash
./scripts/run_encoder_matrix.sh
```

The matrix measures an external encoder's rate-distortion behavior. It does **not** integrate the C++ motion search into libx265 or prove that the custom algorithm changes its performance. See `docs/EXPERIMENT_PROTOCOL.md` for metrics and methodology.

### Optional API

```bash
uvicorn codec_lab.api:app --app-dir python --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` locally.

## Initial synthetic result

On the included 192×128 synthetic test, with 16×16 blocks and a search range of 8 pixels, predictor-guided diamond search evaluated roughly 14 candidates per block versus 235 for exhaustive search. The observed speed/quality tradeoff is specific to this synthetic pair and machine. Do not interpret it as a general encoder-speedup result.

See `results/benchmark.csv`, `results/benchmark_runs.csv`, `results/report/SUMMARY.md`, [the quality/complexity SVG](results/report/quality_complexity.svg), and [the example encoded-video rate–distortion SVG](results/encoder_rd_demo.svg) for supplied example outputs. Re-run locally before making any hardware-dependent timing claims.

## Repository map

```text
cpp/                  C++ motion estimation core and unit tests
python/codec_lab/     benchmark runner, reports, API, encoder matrix
scripts/              reproducible demo commands
data/demo/            generated PGM test pair (created by the demo script)
docs/                 experiment protocol, interview notes, roadmap
results/              example CSVs, plots, and summary
.github/workflows/    CI build and tests
```

## Limitations and research roadmap

Next steps are multi-clip benchmarking, block-size/search-range sweeps, motion/texture diagnostics, raw YUV support, an external VTM/VVenC adapter, and eventual codec integration with baseline-versus-modified end-to-end measurements. See `docs/ROADMAP.md` and `docs/INTERVIEW_WALKTHROUGH.md`.

## Reproducibility notes

Benchmark times depend on machine load, compiler, flags, and runtime environment. Preserve raw runs, report medians, and compare quality as well as complexity. For claims about real HEVC/VVC efficiency, record codec version/configuration and demonstrate a complete baseline-versus-modified encode/decode experiment.

## License

See [LICENSE](LICENSE).

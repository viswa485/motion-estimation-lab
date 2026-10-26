# Motion Estimation Lab

**A reproducible C++17 and Python research prototype for evaluating block-matching motion-search algorithms.**

The project isolates a performance-critical decision in inter-frame video coding: where should an encoder search in the reference frame for the best match to a current block? It compares exhaustive full search with three faster strategies, measuring candidate evaluations, residual error, motion-compensated PSNR, and wall-clock runtime.

> **Scope:** This repository implements standalone block matching, not a complete HEVC/VVC encoder. The C++ search has not been integrated into HM, VTM, VVenC, or libx265. Local SAD and motion-compensated PSNR measurements do not establish encoded bitrate, encoded-video PSNR, BD-rate, or end-to-end encoder speedup.

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

### Optional encoded-video rate–distortion experiment

Install FFmpeg with `libx265` support, then run:

```bash
./scripts/run_encoder_matrix.sh
```

The matrix measures an external encoder's rate–distortion behavior independently of the C++ search implementation. It does not measure the effect of the custom search algorithms on encoder performance. See `docs/EXPERIMENT_PROTOCOL.md` for metrics and methodology.

### Optional API

```bash
uvicorn codec_lab.api:app --app-dir python --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` locally.

## Example benchmark

On the included 192×128 synthetic frame pair, using 16×16 blocks and a search range of 8 pixels, predictor-guided diamond search evaluated about 14 candidates per block, compared with 235 for exhaustive search. This result is specific to the input and configuration; it does not establish a general encoder-speedup result.

See `results/benchmark.csv`, `results/benchmark_runs.csv`, `results/report/SUMMARY.md`, [the quality/complexity plot](results/report/quality_complexity.svg), and [the encoded-video rate–distortion plot](results/encoder_rd_demo.svg) for example outputs. Absolute runtime comparisons should be reproduced on the target hardware.

## Repository map

```text
cpp/                  C++ motion estimation core and unit tests
python/codec_lab/     benchmark runner, reports, API, encoder matrix
scripts/              reproducible demo commands
data/demo/            generated PGM test pair (created by the demo script)
docs/                 experiment protocol and research roadmap
results/              example CSVs, plots, and summary
.github/workflows/    CI build and tests
```

## Limitations and research roadmap

The roadmap covers multi-clip benchmarking, block-size and search-range sweeps, motion/texture diagnostics, raw YUV support, an external VTM/VVenC adapter, and codec-level evaluation. See `docs/ROADMAP.md` for details.

## Reproducibility notes

Benchmark times depend on machine load, compiler settings, and runtime environment. Raw runs and median measurements are retained to make runtime variability visible. Evaluating HEVC/VVC efficiency requires a complete baseline-versus-modified encode/decode experiment with the codec version, configuration, and measurement procedure documented.

## License

See [LICENSE](LICENSE).

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pip install --no-build-isolation -e .
python3 -m codec_lab.data --output-dir data/demo
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 -m codec_lab.runner --build --reference data/demo/reference.pgm --current data/demo/current.pgm --output results/benchmark.csv --block-size 16 --search-range 8 --algorithm all --repeats 5
python3 -m codec_lab.report results/benchmark.csv --output-dir results/report
printf '\nDemo complete.\nCSV: %s/results/benchmark.csv\nReport: %s/results/report/SUMMARY.md\n' "$ROOT" "$ROOT"

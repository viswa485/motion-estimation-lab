#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -f data/demo_source.mp4 ]]; then
  python3 -m codec_lab.demo_video --output data/demo_source.mp4 --frames-dir data/demo_video_frames
fi
python3 -m codec_lab.encoder_matrix --input data/demo_source.mp4 --output results/encoder_rd_demo.csv --crf 22 27 32 37 --preset medium --encoder libx265 --repeats 3
python3 -m codec_lab.encoder_report results/encoder_rd_demo.csv --output results/encoder_rd_demo.svg

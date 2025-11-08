# Benchmark summary

This report measures block-matching search cost and motion-compensated reconstruction quality on the supplied grayscale frame pair. PSNR is a motion-compensation proxy, **not encoded-video PSNR or BD-rate**.

Input: results/benchmark.csv

## Results

| algorithm | avg candidates per block | avg SAD per pixel | motion-compensated PSNR (dB) | elapsed time (ms) |
|---|---:|---:|---:|---:|
| predictive_diamond | 14.0729 | 1.8350 | 32.8004 | 0.8539 |
| diamond | 22.5521 | 3.2040 | 29.9705 | 1.5085 |
| three_step | 26.2500 | 5.0098 | 24.7282 | 1.2377 |
| full_search | 235.0000 | 1.8063 | 32.8714 | 10.2609 |

## Interpretation checklist

- Compare candidate evaluations before interpreting wall-clock time; runtime is sensitive to the machine and build.
- Full search is the exact minimum-SAD baseline within the configured square window.
- Fast searches can miss that minimum; quantify the quality/complexity trade-off across multiple clips and search ranges.
- These measurements do not demonstrate encoder bitrate savings. Validate in a complete encoder before making that claim.

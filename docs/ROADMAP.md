# Research roadmap and truthful commit history

The requested September–November 2025 dates are already in the past. This project snapshot is being published now; do not backdate commits or imply it existed on those dates.

## Follow-on milestones

| # | Suggested commit message | Acceptance criteria |
|---|---|---|
| 1 | feat: add multi-clip benchmark manifest | Run at least five diverse clips; preserve per-clip results and metadata |
| 2 | feat: add block-size and search-range sweep | Automate a parameter matrix and summarize results |
| 3 | feat: add motion and texture diagnostics | Record per-block motion magnitude, local texture, residual distribution, and failure cases |
| 4 | feat: support raw YUV sequence inputs | Define pixel format, bit depth, and dimensions explicitly; test frame alignment |
| 5 | feat: add external VVC encoder baseline adapter | Detect and run a local VVenC/VTM toolchain; record exact version/configuration and output logs |
| 6 | feat: compare rate-distortion curves across configurations | Compare named encoder configurations over multiple quality points and sequences; document BD-rate method and validity range |
| 7 | perf: optimize SAD kernels with equivalence tests | Add early termination or SIMD only behind correctness tests and benchmark the change |
| 8 | research: integrate search experiment into a codec fork | Patch a specific codec version, build it, run encoding/decoding tests, and compare baseline versus modified encoder end-to-end |

For each future commit, write the code, test it, record results, and commit with the actual date. Do not make claims about future integration until the patch and experiment exist. Recruiters care more about reproducible experiments and your ability to explain their limitations than about commit dates spaced across a calendar.

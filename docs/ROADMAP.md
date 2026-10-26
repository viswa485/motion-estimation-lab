# Roadmap

This roadmap describes possible extensions to the current standalone motion-estimation benchmark. Planned work is not part of the implemented feature set until it is reflected in the source code, tests, and results.

| Area | Planned work | Completion criteria |
|---|---|---|
| Dataset coverage | Add a multi-clip benchmark manifest | Evaluate at least five diverse clips and retain per-clip results and metadata |
| Parameter evaluation | Add block-size and search-range sweeps | Run a documented parameter matrix and summarize the results |
| Motion diagnostics | Record motion magnitude, local texture, residual distributions, and failure cases | Produce per-block diagnostics and identify cases where fast search loses quality |
| Input formats | Add raw YUV sequence support | Validate pixel format, bit depth, dimensions, and frame alignment |
| VVC baselines | Add an adapter for an available VVenC or VTM toolchain | Record the exact encoder version, configuration, command, and output logs |
| Rate–distortion analysis | Compare named encoder configurations across quality points and sequences | Document the calculation method, overlap range, and validity of any BD-rate result |
| Search optimization | Evaluate early termination or SIMD SAD kernels | Preserve equivalence tests and include repeatable benchmarks |
| Codec integration | Integrate a search strategy into a specific codec version | Build the modified codec, pass encoding/decoding tests, and compare it against a matched baseline |

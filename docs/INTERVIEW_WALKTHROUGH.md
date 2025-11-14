# Interview walkthrough: Motion Estimation Lab

Use this as a technical guide, not as a script to claim work you have not performed. Be precise about the distinction between this research prototype and a complete HEVC/VVC encoder.

## 90-second project explanation

“I built a C++17 block-matching experiment to study the speed–quality trade-off in motion estimation. It compares exhaustive search against three-step, diamond, and median-predictor-guided diamond search. Python generates a deterministic translated frame pair, runs the compiled binary repeatedly, collects CSV metrics, and generates plots. I use candidate evaluations per block as an algorithmic complexity measure and motion-compensated PSNR plus SAD as local quality measures. Separately, I added an FFmpeg-based HEVC rate–distortion harness that records bitrate, decoded-video PSNR, and repeated encode-time measurements across CRF settings. The current C++ search implementation is standalone; it does not yet modify HM, VTM, VVenC, or libx265. I keep local motion-compensation metrics distinct from encoded-video metrics, and I would only make a BD-rate or encoder-speedup claim after integrating the algorithm into a complete encoder and running controlled baseline-versus-modified tests.”

## Questions to prepare

### Why compare against full search?

Full search enumerates every legal integer displacement in the configured square window, so it gives the minimum SAD over that defined candidate set. It is expensive but a useful local reference. A faster method should be evaluated both by search work saved and by how much residual quality it gives up.

### What is the difference between SAD and rate-distortion cost?

SAD is the sum of absolute pixel differences between the current block and a candidate reference block. It is inexpensive and useful for motion search. Full codec rate-distortion optimization is broader: it combines a distortion term with a rate estimate and includes coding choices and syntax costs. SAD alone is not a complete encoder RDO cost.

### Why can a fast search lose quality?

Fast searches inspect only selected locations and can converge to a local minimum or skip the best displacement. The result depends on texture, motion magnitude, block size, search range, initialization, and search pattern. Report results over varied clips rather than only a synthetic translation.

### What does predictor-guided diamond search test?

It initializes local search using the component-wise median of the left, top, and top-right spatial motion vectors. The hypothesis is that nearby blocks often have correlated motion. It can fail at boundaries, scene changes, occlusions, or motion discontinuities, so compare it to both zero-initialized diamond search and full search.

### Why candidate count in addition to runtime?

Candidate count is a more direct algorithmic-work proxy and is less dependent on machine load and compiler differences. Wall-clock time matters too, but report repeated runs, compiler/build type, CPU, and input dimensions before asserting a speedup.

### How would you move from this prototype to an encoder result?

1. Identify the exact motion-search routine and interfaces in the selected encoder version.
2. Keep a clean baseline build and a patch branch; document compiler flags and configuration.
3. Integrate the search strategy without changing unrelated coding tools.
4. Use a documented multi-sequence test set and common encoding configurations.
5. Encode at multiple QP/quality points, decode outputs, record bitstream sizes and objective quality, and compare rate-distortion curves.
6. Report encode time, quality/bitrate changes, repeated-run methodology, and failures—not only the best sequence.
7. Validate bitstream conformance and make the patch reproducible.

## Claims currently supported

- Implemented C++ block matching with four search strategies.
- Built deterministic synthetic input generation and benchmark automation.
- Recorded search candidate count, selected SAD, motion-compensated PSNR, and runtime.
- Added build/test automation and a local API option.
- Added a separate FFmpeg/libx265 evaluation harness for bitrate, decoded-video PSNR, and repeated encoding-time measurements.

## Claims requiring further evidence

- “Improved HEVC/VVC BD-rate by X%.” Requires full encoder experiments and explicit, reproducible rate-distortion methodology.
- “Integrated into VTM/HM/VVenC/libx265.” Requires an actual patch against a specific upstream version and successful build/encoding tests.
- “Reduced encoder runtime by X%.” Requires repeated end-to-end encoder measurements under controlled settings.

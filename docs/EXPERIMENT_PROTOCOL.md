# Experimental protocol

## Objective

Measure the local quality/complexity trade-off of block-matching motion search. The controlled baseline is exhaustive search over the same legal displacement window.

## Benchmark configuration

- Format: 8-bit grayscale PGM.
- Demo sequence: deterministic textured still frame plus a known integer translation.
- Algorithms: full search, three-step, diamond, and predictor-guided diamond.
- Primary complexity measure: unique candidate evaluations per block.
- Secondary measures: selected SAD per pixel, assembled motion-compensated PSNR, elapsed wall-clock time.

## Procedure

1. Use the same two frames, block size, search range, build type, and machine for each compared algorithm.
2. Run multiple repetitions when discussing runtime; report median and spread rather than selecting the fastest single run.
3. Keep the full-search output as the exact minimum-SAD reference for each block's legal square window.
4. Include all evaluated algorithms and retain adverse results. Select the evaluation corpus before reviewing comparative outcomes.
5. Evaluate a varied corpus containing low- and high-texture regions, panning, occlusion, scene cuts, and noise before generalizing results.
6. Evaluate encoder-level performance with a complete encoder/decoder pipeline and matched quality/bitrate operating points. The current metrics do not support a BD-rate conclusion.

## Threats to validity

- A synthetic translated frame is an algorithm sanity check, not a representative video corpus.
- Block matching with SAD does not model all codec costs (syntax bits, transforms, quantization, prediction modes, or full RDO).
- Search implementations have different memory-access patterns and branch behavior; candidate count is a complexity measure, not a direct runtime estimate.
- The chosen displacement window defines the full-search optimum; it is not the global optimum outside that window.
- Border blocks and content clamping influence edge results.

## Optional full-encoder rate-distortion matrix

The encoder matrix runs an external FFmpeg encoder across CRF points and records container-size bitrate, decoded-video PSNR against the supplied input, and median encode time over repeated runs. This is a real encoding experiment, but it remains separate from the custom C++ motion-search code.

- The sample clip is generated deterministically by the helper script and requires FFmpeg with H.264 encoding support.
- For robust comparisons, use uncompressed or visually lossless source footage, align dimensions, frame rate, and frame count, record FFmpeg and encoder versions, and use the same source and machine settings.
- A CRF curve from one encoder is not a BD-rate comparison. BD-rate requires a defensible rate-distortion comparison between two defined encoder configurations over matched quality ranges and a documented calculation method.
- Encode-time results should use repeated measurements; the matrix records the median and spread. Results from the external libx265 run do not measure the C++ search algorithms. That requires a corresponding encoder integration and a controlled end-to-end comparison.

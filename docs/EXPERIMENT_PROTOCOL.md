# Experimental protocol

## Objective

Measure the local quality/complexity trade-off of block-matching motion search. The controlled baseline is exhaustive search over the same legal displacement window.

## Initial experiment

- Format: 8-bit grayscale PGM.
- Demo sequence: deterministic textured still frame plus a known integer translation.
- Algorithms: full search, three-step, diamond, and predictor-guided diamond.
- Primary complexity measure: unique candidate evaluations per block.
- Secondary measures: selected SAD per pixel, assembled motion-compensated PSNR, elapsed wall-clock time.

## Procedure

1. Use the same two frames, block size, search range, build type, and machine for each compared algorithm.
2. Run multiple repetitions when discussing runtime; report median and spread rather than selecting the fastest single run.
3. Keep the full-search output as the exact minimum-SAD reference for each block's legal square window.
4. Report all algorithms, including cases where the fast method loses on quality. Do not remove difficult sequences after seeing the result.
5. Extend the corpus with low-texture, high-texture, panning, occlusion, scene-cut, and noisy clips before generalizing.
6. For an encoder-level claim, use a complete encoder/decoder pipeline and matched quality/bitrate operating points. This repository's metrics alone cannot support a BD-rate claim.

## Threats to validity

- A synthetic translated frame is an algorithm sanity check, not a representative video corpus.
- Block matching with SAD does not model all codec costs (syntax bits, transforms, quantization, prediction modes, or full RDO).
- Search implementations may have different access patterns and branch behaviour; candidate count does not equal runtime exactly.
- The chosen displacement window defines the full-search optimum; it is not the global optimum outside that window.
- Border blocks and content clamping influence edge results.

## Optional full-encoder rate-distortion matrix

The encoder matrix runs an external FFmpeg encoder across CRF points and records container-size bitrate, decoded-video PSNR against the supplied input, and median encode time over repeated runs. This is a real encoding experiment, but it remains separate from the custom C++ motion-search code.

- The provided sample clip is generated deterministically by the helper script and requires FFmpeg with H.264 encoding support.
- For publishable comparisons, start from uncompressed or visually lossless source footage, keep dimensions/frame rate/frames aligned, record FFmpeg and encoder versions, and compare the same source and machine settings.
- A CRF curve from one encoder is not a BD-rate comparison. BD-rate requires a defensible rate-distortion comparison between two defined encoder configurations over matched quality ranges and a documented calculation method.
- Encode-time results should be based on repeated measurements; this tool records median and spread. Do not make claims about the C++ search algorithms from libx265 results until the relevant search modification is integrated into that encoder and the baseline/modified builds are compared end-to-end.

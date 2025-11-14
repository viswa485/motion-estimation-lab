# Publishing and maintenance notes

## Local development

Run the README quick start and verify the C++ tests, Python tests, and optional FFmpeg experiment before sharing the repository. Replace or add to the demo experiments only with results you can explain.

## Commit discipline

Use the roadmap for commit-sized milestones. Commit after completing and validating each improvement, with the actual date and a message that describes the change. Do not create backdated commits to simulate work that did not occur.

## Before sharing with recruiters

- Confirm GitHub Actions has a passing run.
- Read the README claims and remove anything you cannot explain line by line.
- Be explicit that the C++ search prototype has not yet been integrated into HM, VTM, VVenC, or libx265.
- Be ready to explain the difference between block SAD, motion-compensated PSNR, encoded-video PSNR, bitrate, and BD-rate.
- Do not claim encoder speedup or BD-rate improvements from this standalone search benchmark.

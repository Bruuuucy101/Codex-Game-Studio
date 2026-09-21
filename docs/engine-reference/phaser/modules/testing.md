# Phaser 3 test evidence

Last verified: 2026-09-21. Test protocol; execution is NOT RUN in Task 1.

Vitest unit tests exercise pure state: bounds, diagonal speed, fixed-step equivalence, collection, independent initial state and reset. Unit discovery stays under `tests/web-unit/**/*_test.ts`; Playwright browser discovery stays under `tests/browser/`.

Run typecheck, units and build before Playwright against the production preview. Use actual keyboard/pointer input and observable HUD/player output to verify movement, collection, reset twice, focus clearing and resize. Assert a real Game and Scene execute, including restart cleanup. Capture screenshots and console/page errors. A test-only deterministic seam may supplement actual input, never replace it or appear as arbitrary mutation APIs in production.

Record package/browser/Node versions, commands, exit codes, counts, screenshots and NOT RUN checks. Chromium software rendering is not Safari, mobile, WebGPU or hardware certification.

Official references: [Vitest configuration](https://vitest.dev/config/), [Playwright web server](https://playwright.dev/docs/test-webserver), [Playwright input](https://playwright.dev/docs/input).

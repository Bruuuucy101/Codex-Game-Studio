# Web game development — Phaser 3 and Three.js

Last updated: 2026-09-21. This is the canonical workflow contract. Runnable
scaffolds and the preview-first copy CLI are included. Runtime evidence is
reported separately in `docs/codex-adapter/validation.md`; source presence does
not certify browser support.

## Select and configure

Use `/setup-engine phaser 3.90.0` or `/setup-engine threejs 0.186.0`. Aliases:
phaser3 → phaser; three / three.js → threejs. Phaser means Phaser 3. Preserve an
existing pin/language; never silently migrate to Phaser 4 or another Three revision.
Write the matching Engine Specialists preferences and VERSION.md import. This
framework remains unconfigured just because it contains reference/template files.

Phaser is the browser-first 2D option. Three.js is a code-first 3D renderer;
application code owns simulation, UI and other game systems. WebGL2 is the Three
baseline; WebGPU is opt-in. Retain Godot, Unity, Unreal and all review modes.

## Reproducible baseline candidates

| Dependency | Exact version |
|---|---|
| Phaser | 3.90.0 |
| Three.js / @types/three | 0.186.0 / 0.186.0 (r186) |
| Vite | 7.3.6 |
| TypeScript | 5.9.3 |
| Vitest | 4.1.11 |
| Playwright | 1.58.2 |
| Node | 22.14.0 |

Exact direct versions and a committed lockfile are required. These are selected
candidates, not newest-version claims. Phaser ships types. Keep Three addons in
the same package; no speculative framework, physics, telemetry, external assets
or billable service. Check installed pins first. Tagged metadata:
[Phaser](https://raw.githubusercontent.com/phaserjs/phaser/v3.90.0/package.json),
[Three](https://raw.githubusercontent.com/mrdoob/three.js/r186/package.json),
[Vite](https://raw.githubusercontent.com/vitejs/vite/v7.3.6/packages/vite/package.json),
[Vitest](https://raw.githubusercontent.com/vitest-dev/vitest/v4.1.11/packages/vitest/package.json),
[TypeScript](https://raw.githubusercontent.com/microsoft/TypeScript/v5.9.3/package.json),
[Playwright](https://raw.githubusercontent.com/microsoft/playwright/v1.58.2/packages/playwright-test/package.json).

## Scaffold interface

Sources: `templates/web/phaser/` and `templates/web/threejs/`. From the framework:
`python3 tools/ccgs_codex.py scaffold-web ENGINE --target PATH [--write]`.
The default previews a deterministic manifest without writes. An authorized
tools-programmer performs copying/build because setup-engine has no Bash tool.
The explicit write preflights all source/destination files and ancestors, rejects
symlinks, traversal, metadata targets and collisions, and never overwrites. A
studio already at the target can coexist with non-conflicting game files. No
force option, dependency installation, configuration selection or external copy
is implicit. Spaces in a target path must be preserved as one argument.

## Application and ownership

Keep `src/core/` pure state, thin engine adapters in `src/scenes/`, and input/HUD
in their owned modules; `assets/data/game.json` is the balance source. Templates,
node_modules, dist, caches and tests are not live source for stage detection.
Phaser shutdown/restart removes owned external listeners/timers while preserving
shared cache ownership. Three owns one loop and explicitly releases owned GPU
resources and renderer on teardown; scene.clear/Object3D.dispose alone do not
release shared geometry/material/texture resources. Read each engine's lifecycle
module. Keep reset distinct from teardown and test repeated use.

## Test and release contract

Run from the adopted game: `npm ci`, `npm run typecheck`, `npm test`,
`npm run build`, then `npm run test:browser`. Install the matching Playwright
Chromium explicitly during dependency setup. Unit discovery is `tests/web-unit/**/*_test.ts`;
browser discovery is `tests/browser/`, with production preview owned by
Playwright. Merge existing scripts/config intentionally rather than overwrite.

Pure tests cover bounds, diagonal speed, fixed-step determinism, collection and
reset with independent state. Browser tests use keyboard/pointer and visible
movement, score, reset twice, focus loss, resize and no page/console errors.
Three must create a real WebGL2 context and nonempty frame. Inspect screenshots.
Never label a mock, typecheck, nonempty canvas element or authored test spec a
successful playtest. Record exact versions/commands/exit codes and NOT RUN gaps.
CI requires Python 3.10/3.12 plus a separate web matrix, with all relevant jobs
blocking release. Browser artifacts are retained for inspection.

Browser limits include asset base paths, CORS/CSP, high DPI, tab throttling,
focus and autoplay. DOM HUD needs keyboard focus, semantics and labels; a canvas
is not automatically accessible. Audio starts from a user gesture. Chromium
software rendering is not native GPU, mobile, Safari or WebGPU certification.
Client storage and shipped keys cannot prove trusted scores; defer server
validation to security-engineer/network-programmer under an accepted threat model.

# Web engine support — design and acceptance

User-authorized extension of the complete studio for upstream issues [#62](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/62) and [#22](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/22). The user delegated product and technical decisions and requested staged tests. This design is approved under that standing delegation.

## Outcome

A developer can select Phaser 3 or Three.js, configure the correct specialist and testing workflow, create a small runnable game, and exercise real movement, collection, reset and resize in a browser. Existing Godot (GDScript/C#/Both), Unity, Unreal, review modes and original workflows remain available. These are two explicit engine choices, not a generic claim to support all web engines.

## Global constraints

- Preserve the 417-file baseline lock byte-for-byte (SHA256 `fb68f5ff2fd503611db210ee6c84e7820865778b4da4275bf5447667a2a72afa`); record every modified baseline file's exact reviewed hash and issue provenance. Never enroll new files into that original lock.
- Preserve all 73 original workflow identities and all 49 original role identities and full role bodies except deliberate documented extensions; regenerate Codex entry points from canonical `.claude/` sources.
- Engine IDs are `phaser` and `threejs`; specialists are `phaser-specialist` and `threejs-specialist`. Aliases `phaser3`, `three` and `three.js` resolve to those IDs.
- Tested baseline candidates are Phaser `3.90.0`, Three.js `0.186.0` (r186), `@types/three` `0.186.0`, Vite `7.3.6`, TypeScript `5.9.3`, Vitest `4.1.11`, Playwright `1.58.2`, Node `22.14.0`. Exact direct versions and committed lockfiles are required. Installed project pins take precedence; do not migrate Phaser 3 to Phaser 4 silently.
- Source presence, deterministic Python tests, sampled agent behavior, browser integration and native hardware testing are distinct evidence. Record actual commands and versions; do not claim mobile/Safari/WebGPU or all engine parity from Chromium.
- No telemetry, external game assets, billable services, global trust/configuration edits or automatic dependency installation by the scaffold helper.

## Architecture

Canonical roles contain complete lifecycle/version/ownership guidance, with engine references and behavioral specs. Setup, implementation, review and testing workflows route consistently. Engine references distinguish officially checked documentation from actually executed tests. Phaser shutdown/restart cleans owned resources; Three.js owns one loop and explicitly disposes owned geometry/material/texture/renderer resources. Shared resources need ownership accounting. WebGL2 is the Three.js baseline; WebGPU is separate opt-in scope. Client storage obfuscation never proves trusted scores.

Templates live under `templates/web/phaser/` and `templates/web/threejs/`; no demo code is installed into this framework's own `src/`. Each contains a small data-driven collect game, pure fixed-step simulation and thin engine/input/HUD integration, exact package lock, build/unit/browser scripts and user instructions. Use `assets/data/game.json` as the single balance source. Keep unit and browser discovery separate. Production artifacts do not expose arbitrary test mutation APIs.

The stdlib CLI adds `scaffold-web ENGINE --target PATH [--write]`. Default is read-only preview with deterministic file manifest. `--write` preflights every enumerated source and destination, rejecting collisions, symlinks in either tree/ancestors, traversal, protected metadata targets and malformed engine names before writes. Existing studio files may coexist, but no file is overwritten and no force option exists. Absolute targets are allowed subject to host permissions; path normalization may not conceal `..`. It copies only declared template files, never `node_modules`, `dist`, browser results, caches or unrelated files. Failure must not damage existing files. It does not install packages or change engine configuration. Setup-engine delegates actual copy/build to an authorized tools-programmer, retaining its original allowlist.

## Acceptance

1. All original identities survive; both new roles, behavioral specs, routing and references resolve; generated bodies match canonical sources and strict provenance passes.
2. Scaffold dry-run has no effects; a clean copy matches the manifest; collisions including late-manifest collisions, source/destination/ancestor symlinks and invalid paths fail safely. Paths with spaces work. Repeated write does not overwrite.
3. Each exact release template is copied to a clean fixture and runs `npm ci`, typecheck, unit tests and production build.
4. Playwright Chromium runs against the production preview, uses actual keyboard/pointer input and verifies visible movement/collection/reset twice, input clearing on focus loss, resize and no console/page errors. Three.js creates an actual WebGL2 context and nonempty frame; capture and inspect screenshots. A test-only deterministic seam may supplement, not replace, actual input.
5. Unit tests cover bounds, diagonal speed, fixed-step determinism, collection and reset, with independent state. Browser tests exercise renderer and input integration.
6. CI runs Python 3.10/3.12 plus separate web matrix jobs. Release publication waits for all relevant jobs. Core adapter remains dependency-free.
7. Stage heuristics recognize actual web code without counting template/vendor trees as a live game. Version/routing traps and restart/disposal are covered in canonical behavioral specs. Documentation records limitations honestly.

## Self-review

The scaffold helper is deliberately a copy operation, not a package manager or engine detector. It remains useful when the target already contains studio files. A coherent setup path is required before describing the feature as supported. Documentation refresh cannot substitute for runtime verification; an unavailable browser remains an explicit acceptance gap.

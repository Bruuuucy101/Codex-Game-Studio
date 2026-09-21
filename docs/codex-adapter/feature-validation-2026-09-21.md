# v0.2.0-beta feature validation — 2026-09-21

This record covers four delivered additions: Phaser, Three.js, tooling and libGDX.
It separates source checks, real filesystem behavior, model samples, engine tests
and publication. Board-sync remains designed but entirely unimplemented; its
plans are not shipped commands, dependencies or acceptance evidence. Creative MCP,
paid asset backends and NPC TTS also remain deferred.

## Source identity and provenance

The unchanged upstream lock covers 417 paths at
`984023ddac0d5e27624f2baacde6105e45de375f`, SHA256
`fb68f5ff2fd503611db210ee6c84e7820865778b4da4275bf5447667a2a72afa`.
All paths remain: 359 original hashes and 58 exact reviewed patch hashes.
The [ledger](../../.codex/upstream-patches.json) describes deliberate changes;
new source files are not added to the original lock.

| Inventory | Current result |
|---|---|
| Workflows | Original 73 identities plus `setup-tool` = 74 |
| Roles | Original 49 plus `phaser-specialist`, `threejs-specialist`, `game-pipeline-developer`, `libgdx-specialist`, `libgdx-scene2d-specialist`, `libgdx-graphics-specialist`, `libgdx-ashley-specialist`, `libgdx-core-specialist` = 57 |
| Other source | 11 rules, 12 hook scripts, 41 recursive document templates, 135 behavioral-framework Markdown files |
| Generated | 133 outputs; all 57 native role profiles and project config parse |

Exact identity subsets/additions are asserted in adapter tests and CI. Counts do
not prove execution of the authored behavioral framework, which was not run
exhaustively. Original Godot/Unity/Unreal branches and full/lean/solo remain present.

## Deterministic and real execution evidence

The final feature source checkpoint is local commit
`c4f77df99ce9bda541fd0e1253247ed7bd12eb41`. Its public candidate
`8b6add131e4e42359b56aece422f806927e2621b` was tested through merge commit
`4fb0ad5938a1c58e15abc7b6200a812d17c7e6fd`, tree
`6e81686e8ac6c6da9a7d1020eaaffb6145a68283`. The controller compared the full
719-file public tree by bytes and intended modes, including the pre-existing
executable hook mode. Release metadata follows this source checkpoint.

[GitHub Actions run 35608239399](https://github.com/Bruuuucy101/Codex-Game-Studio/actions/runs/35608239399)
passed **verify (3.10), verify (3.12), web (phaser), web (threejs), libgdx**.
The PR release job was skipped. It is candidate evidence, not final main evidence.

| Layer | Actual observed result | Boundary |
|---|---|---|
| Adapter | 128 tests pass; strict provenance and generated integrity pass; 57 TOMLs parse | Source assertions and filesystem tests do not certify model adherence |
| Web | Each starter: typecheck, 10 unit tests, production build, 4 real Chromium tests on Linux; initial/narrow/restored screenshots inspected | macOS Chromium aborted before page load; no bypass. Persisted page-event contract tested, not actual history BFCache eligibility; Safari/mobile/WebGPU/audio/gamepad unverified |
| Tool sample | Actual stdlib CSV converter twice produced identical JSON, exit 0; malformed data, no-overwrite and a real competing-writer reservation tested | Text schema only; no native engine binary import/conversion or provider execution |
| libGDX | Clean 24-file copy matched exact bytes/modes; 7 pure + 3 real HeadlessApplication tests, desktop installDist and finite runner passed locally and in Linux CI | Packaging/headless do not verify GPU frames, input feel or audio; mobile/GWT/Kotlin/KTX/Ashley/Box2D unverified |

Adapter commands from the repository root:

```sh
python3 tools/ccgs_codex.py generate
python3 tools/ccgs_codex.py check --strict-upstream
python3 -m unittest discover -s tests/codex_adapter -v
git diff --check
```

Web CI used Node 22.14.0, Phaser 3.90.0, Three.js 0.186.0/r186,
Playwright 1.58.2, TypeScript 5.9.3, Vite 7.3.6 and Vitest 4.1.11.
After clean `scaffold-web ENGINE --target PATH --write`, inside each target:

```sh
npm ci
npm run typecheck
npm test
npm run build
npx playwright install --with-deps chromium
npm run test:browser
```

libGDX local acceptance used macOS 13.7.8 x86_64, Temurin 21.0.12.1+1,
Gradle 8.14.3, libGDX 1.14.2 and JUnit Jupiter 5.13.4. Linux CI used JDK 21.
After clean `scaffold-libgdx --target PATH --write`, inside the copied target:

```sh
./gradlew :core:test :headless:test :lwjgl3:installDist --no-daemon
./gradlew :headless:run --no-daemon
```

The local clean run additionally used `--no-watch-fs --offline` with a populated
cache, without rewriting locks. Runner output: `Collected signal; score=1`.
The [portable libGDX receipt](libgdx-evidence.json) records all 24 template hashes,
wrapper provenance, commands and test results. JDK 21 emitted Java 8 target warnings.
The wrapper's embedded license and [third-party notices](../../templates/libgdx/THIRD-PARTY-NOTICES.md)
are retained; external packages are not relicensed as MIT adaptation code.

CSV input SHA256 before/after:
`37cb8abe05802979e41111e54ec7e82018dff646cee6b49e7fa1aafaa130ec26`.
Both output SHA256 values:
`329d5c9dc9ec70198862a72f6a3b600ddacd86addd445fc1fd98a19b761c669d`.
See the [executable example](../../examples/tooling/level-exporter/README.md).

## Five fresh-agent observations

These were actual fresh-agent runs on isolated fixture copies with explicit
workflow entry loading and bounded user instructions. They are neither native
role-discovery certification nor statistical reliability measurements.

- **Standalone tool setup:** wrote the canonical tool contract and explicit tooling
  marker/stage, kept engine-agnostic intent and lean mode. The earlier baseline
  had written a generic project specification/Concept; it already respected
  no-engine/lean, so those are preserved behavior rather than new fixes.
- **Mixed game/tool setup:** added a component contract while keeping Godot game
  engine, Production stage, review mode and user game files intact. Only the
  authorized Tooling preference section changed within existing game preferences.
- **Phaser setup:** configured the selected pinned engine and full mode; exactly
  five authorized configuration/reference/session paths changed, user files intact.
- **Three.js consultation:** retained the existing project pin and explained
  resource ownership read-only; zero files changed.
- **libGDX setup/consultation:** configured the selected engine and lean mode,
  distinguished headless checks from rendering; exactly five authorized paths
  changed, user files intact.

Tooling samples used commit `c56913a1506c6b02068ea6fd6979887d60afdfc1`;
engine samples used `c4f77df99ce9bda541fd0e1253247ed7bd12eb41`.
Whole-fixture comparisons confirmed the engine samples changed exactly 5/0/5 paths
and all other source bytes remained intact. Engine setup changes were limited to
`CLAUDE.md`, `.claude/docs/technical-preferences.md`, the selected engine's
`VERSION.md`, `production/review-mode.txt` and `production/session-state/active.md`.
Tooling report SHA256:
`f76d542a9debcb6cf75826551f1765a89f6e7f7a77fff685b7d52504d4adffaf`;
engine report SHA256:
`fd741b5bbe678e1b2b964af76ae9d822f9b705ffc87fd9afb83c6d91a7f1e9f8`.
An earlier contaminated engine attempt is excluded. No actual specialist
implementation, delegation/reviewer execution, engine run or GPU test is claimed
from these setup/consultation samples; runtime receipts above are separate.

## Release boundary

Task-scoped implementation reviews and their correction reviews are complete at
the recorded feature checkpoint. Aggregate release review, final main CI and
published tag/ZIP verification are later gates. The workflow requires all five
matrix/job results before publishing from the public repository's main branch;
a PR cannot publish. Existing exact tags/releases remain unchanged, API failures
abort, and a concurrent create conflict fails rather than overwrites assets.

Expected archive is `Codex-Game-Studio-v0.2.0-beta.zip`, with root
`Codex-Game-Studio/` and `SHA256SUMS.txt`. Actual final publication must verify the
tag target, checksum and every archived Git blob/mode/inventory against main.
This document does not assert those future gates passed. Inspect [Actions](https://github.com/Bruuuucy101/Codex-Game-Studio/actions)
and [releases](https://github.com/Bruuuucy101/Codex-Game-Studio/releases) for the
published status. [Earlier validation](validation.md) retains historical results
with their original scope; current counts must not be retroactively applied to them.

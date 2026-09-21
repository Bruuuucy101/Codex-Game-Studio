# v0.2.0-beta

Four additions to the community Codex adaptation of [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios):

- [Phaser 3 support (#62)](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/62) and [Three.js support (#22)](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/22): two complete specialists, version-aware workflows and pinned TypeScript collect-game starters. `python3 tools/ccgs_codex.py scaffold-web phaser --target my-web-game` previews the copy; `threejs` selects Three.js.
- [Tooling projects (#19)](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/19): `ccgs-setup-tool` authors, updates or adopts `tools/TOOL_SPEC.md`; standalone tools receive their own stage, while game components retain the game configuration. A pipeline developer role and safe CSV-to-JSON example accompany the workflow.
- [libGDX support (#105)](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/105): five specialists, Java/Kotlin-aware module guidance and a pinned Java core/lwjgl3/headless starter. `python3 tools/ccgs_codex.py scaffold-libgdx --target my-java-game` previews the copy. Its actual headless lifecycle tests and desktop packaging are verified separately from GPU playtests.

Both scaffold commands require `--write` to copy; they never overwrite files or install packages. Current inventory is **74 workflows and 57 roles**, preserving all original 73/49 identities, 417 baseline paths, original lock bytes, engine branches and full/lean/solo modes. Of the baseline files, 359 retain original bytes and 58 have exact reviewed patches. Earlier issue fixes remain included.

Acceptance before release metadata: **128 adapter tests**, **57 parsed role profiles**, **10 unit + 4 Chromium browser tests per web starter**, **7 pure + 3 actual libGDX headless tests**, desktop packaging and the finite runner. Five fresh-agent samples exercised standalone/mixed tooling setup, Phaser setup, a read-only Three.js consultation and libGDX setup. These evidence layers have different scopes; see [current feature validation](docs/codex-adapter/feature-validation-2026-09-21.md) and the [34-issue audit](docs/codex-adapter/upstream-issues-2026-09-21.md).

[Candidate CI run 35608239399](https://github.com/Bruuuucy101/Codex-Game-Studio/actions/runs/35608239399) passed all five required jobs on the recorded feature tree; the PR release job correctly skipped. Final main CI, tag and downloaded ZIP verification remain separate publication gates, not completed results asserted here. The release workflow waits for both Python versions, both web engines and libGDX; it preserves an existing version tag or release. Archive: `Codex-Game-Studio-v0.2.0-beta.zip`, root `Codex-Game-Studio/`, checksum file `SHA256SUMS.txt`.

Board-sync [#82](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/82) remains designed but unimplemented: no snapshot/setup/sync command or dependency ships. Creative MCP #40, paid vendor backends #23 and NPC TTS #14 also remain deferred. No provider execution, mobile/Kotlin/KTX/GWT/WebGPU support validation, libGDX GPU playtest, all-workflow reliability or official upstream issue closure is claimed.

Use Python 3.10+, Git and Bash; web starters need Node >=22.12.0 (CI 22.14.0), and the Java starter needs JDK 21. Read the [English quickstart](.github/README.md), [Chinese quickstart](README-CODEX.zh-CN.md) and [upgrade guide](UPGRADING.md). Original copyright/MIT license: Donchitos; adaptation additions: Bruuuucy101. External dependencies retain their own licenses, including the official Apache-2.0 Gradle wrapper; see [third-party notices](templates/libgdx/THIRD-PARTY-NOTICES.md).

## Historical release records

# v0.1.1-beta

Reviewed upstream issue fixes for the community Codex adaptation of [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) by Donchitos. All 73 workflows, 49 roles, engine branches and review modes remain available.

- Correct hotfix authorization order, narrative approval checkpoint, sprint review-mode consistency and the architecture skill heading.
- Read large ADRs in bounded sections; validate current Accepted status and per-file SHA256 before reusing story summaries. Explicit role routing keeps decisions with the coordinator and uses real delegation.
- Audit runnable sprint prerequisites and capacity, document selective baseline-aware updates, and align two inherited behavior specifications with the actual implementation/review lifecycle.
- Preserve all 417 original paths: 407 unchanged and 10 explicitly reviewed source corrections. The original source lock and license remain unchanged. Strict checks accept only baseline bytes or exact recorded patches.
- Record dispositions for all 34 open upstream issues. New engine/vendor integrations remain separate feature requests. No claim is made that upstream issues were closed.

Local acceptance: **73 deterministic adapter tests**, **six real Git update fixtures**, and **three isolated fresh-agent samples** (denied hotfix implementation, stale summary with a 420,571-character current ADR, and missing runnable-demo prerequisites). These are separate evidence layers; see the [validation report](docs/codex-adapter/validation.md) and [issue audit](docs/codex-adapter/upstream-issues-2026-09-21.md).

This remains a beta. Native role selection, automatic trusted hook execution, all-workflow reliability and actual game-engine builds are not certified. CI and release publication are verified separately in [GitHub Actions](https://github.com/Bruuuucy101/Codex-Game-Studio/actions); these local results do not claim that a release job has already succeeded. The release workflow creates this version only if absent and leaves the earlier beta unchanged.

Use Python 3.10+, Git, Bash and a Codex host supporting the selected model. Open the cloned repository root and follow the [Chinese quickstart](README-CODEX.zh-CN.md) or [English guide](.github/README.md). Original copyright and MIT license: Donchitos. Adaptation additions under MIT: Bruuuucy101.

## Previous release record

# v0.1.0-beta

First public beta of the community Codex adaptation of [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) by Donchitos.

- Preserve all 417 original files from upstream commit `984023ddac0d5e27624f2baacde6105e45de375f`, including the original license.
- Add 73 complete-source skill routes, 49 full-body role configurations, rule loading, hook bridging and project-local runtime instructions.
- Add generation, integrity checks, diagnostics, status and role/workflow inspection commands.
- Include 34 deterministic tests, source digests, sampled behavioral evidence and a Chinese quickstart.

This is a beta, not a claim of complete runtime equivalence. Live hooks require project/hook trust; native custom-role selection varies by host; notifications, status UI and hard role-policy enforcement have documented differences. Actual game-engine builds and end-to-end production workflows remain unverified.

Use a Codex version supporting your selected model. Start with a fresh project, read `.github/README.md` or `README-CODEX.zh-CN.md`, and run the diagnostics before initializing your game.

Original project copyright: Donchitos. Codex adaptation additions: Bruuuucy101. Both are distributed under MIT with attribution retained.

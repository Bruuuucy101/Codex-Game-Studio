## Additional libGDX support — 2026-09-21

Five libGDX specialists and version references now support Java/Kotlin-aware
workflow routing and Gradle module paths. The preview-first starter copier ships
an official checksum-pinned wrapper, strict dependency locks, a data-driven Java
collect game, actual headless lifecycle tests and a desktop distribution build.
Current inventory: 74 workflows and 57 roles, retaining all original 73/49 identities.
GPU/device playtests and optional Kotlin/KTX/mobile/GWT/ECS/physics remain separate
validation. The records below describe their original release scope; current
acceptance and limitations are in docs/codex-adapter/validation.md.

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

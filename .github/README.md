# Codex Game Studios

**A community-maintained Codex adaptation of [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) by Donchitos.**

75 workflow skills, 57 specialist roles, and the original studio's design, implementation, review and QA processes, with a project-local Codex compatibility layer.

**Version: v0.2.0-beta.** Original source coverage is verified; complete runtime equivalence across every workflow, host and game engine is not. This is not an official release from Donchitos, Anthropic or OpenAI.

[中文使用指南](../README-CODEX.zh-CN.md) · [Capability inventory](../docs/codex-adapter/capabilities.md) · [Validation report](../docs/codex-adapter/validation.md) · [Release notes](../RELEASE_NOTES.md)

## What is preserved

The baseline is upstream commit [`984023d`](https://github.com/Donchitos/Claude-Code-Game-Studios/tree/984023ddac0d5e27624f2baacde6105e45de375f). All 417 baseline files are retained: 359 remain byte-for-byte intact, and 58 have explicit reviewed changes recorded in the [patch ledger](../.codex/upstream-patches.json). The original lock and MIT license are unchanged. The upstream-derived README remains at the repository root; this GitHub landing page describes the Codex adaptation.

| Original capability | Codex adaptation |
|---|---|
| 73 workflows | Namespaced `ccgs-*` skills that load each complete original workflow |
| 49 roles | Full original role bodies in Codex profiles, with a real-subagent fallback |
| 11 path-scoped rule sets | Original rules loaded before edits and injected through supported hooks |
| 12 hook scripts | All retained; 11 scripts bridged, with notification differences documented |
| 40 template files | All preserved, including nested templates |
| Godot, Unity and Unreal workflows | Original engine branches, specialists and references retained |
| Full, lean and solo review modes | Original gates, evidence requirements and recovery instructions retained |

## Quick start

Requirements: a Codex host supporting project skills and real subagent delegation, Python 3.10+, Git and Bash. Use a Codex version that supports your selected model. Adapter checks ran on macOS; web browser and libGDX CI ran on Linux. Native Windows and unlisted engine/platform combinations remain unverified.

1. Clone this repository and open the cloned directory itself as a Codex project. A downloaded ZIP needs `git init` in its root before the hook commands can locate the project.
2. Review and trust the project and its hooks through Codex's normal `/hooks` flow. No script automatically changes your trust or approval settings.
3. Ask Codex: `Use ccgs-help to explain the studio workflows.`
4. Start a game with: `Use ccgs-start and guide me through the original studio process.` You can also select `$ccgs-start` where skill selection is supported.

Choose your game concept and engine through that workflow. Start in a fresh project; do not overwrite an existing game's files with this template.

## v0.2.0-beta project choices

Ask Codex `Use ccgs-setup-engine phaser 3.90.0`, `Use ccgs-setup-engine threejs 0.186.0`, or `Use ccgs-setup-engine libgdx 1.14.2`. Existing project pins take precedence. For an engine-agnostic tool, ask `Use ccgs-setup-tool level-exporter author --review lean`; `update` and `adopt` handle existing contracts. Start path E also leads to tooling. Setup writes an authorized specification, not an implemented tool. Components inside games preserve game configuration and stage. All original engines and full/lean/solo modes remain available.

From the studio root, preview one starter into a child directory (targets are relative to the current directory):

```sh
python3 tools/ccgs_codex.py scaffold-web phaser --target my-web-game
python3 tools/ccgs_codex.py scaffold-web threejs --target my-three-game
python3 tools/ccgs_codex.py scaffold-libgdx --target my-java-game
```

Append `--write` to the chosen command after checking the preview. Copying refuses collisions/symlinks, preserves existing files and never installs dependencies. Run subsequent commands **inside the copied target**:

- Web: Node >=22.12.0 and npm (CI Node 22.14.0). Run `npm ci`, `npm run typecheck`, `npm test`, `npm run build`; `npm run dev` launches locally. For Chromium evidence run `npx playwright install --with-deps chromium` then `npm run test:browser`. Installation downloads packages/browser dependencies.
- libGDX: JDK 21; included Gradle 8.14.3 wrapper and strict locks. Run `./gradlew :core:test :headless:test :lwjgl3:installDist --no-daemon` and `./gradlew :headless:run --no-daemon`. First use downloads the checksum-pinned distribution and Maven dependencies. Windows uses `gradlew.bat` but is unverified. Desktop packaging/headless tests do not prove GPU/input/audio behavior. See [starter instructions](../templates/libgdx/README-LIBGDX.md).
- Tooling: the bundled [CSV converter](../examples/tooling/level-exporter/README.md) uses Python 3.10+ and the standard library; no engine or provider is required. Its deterministic processing tests are separate from sampled setup behavior.

Mobile, Kotlin/KTX/GWT, WebGPU and external provider execution remain unverified. Board-sync is designed but unimplemented, with no commands or dependency shipped. [Feature validation](../docs/codex-adapter/feature-validation-2026-09-21.md) separates source checks, model samples, actual engine execution and pending publication verification. External packages retain their own licenses; see [wrapper/dependency notices](../templates/libgdx/THIRD-PARTY-NOTICES.md).

## Verify the adapter

Run these commands from the repository root:

```sh
python3 tools/ccgs_codex.py doctor
python3 tools/ccgs_codex.py check --strict-upstream
python3 -m unittest discover -s tests/codex_adapter -v
```

Historical v0.1.1-beta passed 73 deterministic adapter tests and six real Git update fixtures. Three fresh-agent samples observed hotfix refusal, current bounded ADR reconciliation and missing demo-prerequisite planning. The initial beta separately exercised real CLI role delegation. See the [34-issue audit](../docs/codex-adapter/upstream-issues-2026-09-21.md) and [validation report](../docs/codex-adapter/validation.md) for scope and limits.

Strict verification accepts pinned bytes or exact reviewed patches; `check --pristine-upstream` intentionally reports this release’s 58 reviewed changes. Game-specific edits may produce additional drift: review it using the [source maintenance guide](../docs/codex-adapter/source-maintenance.md). Current candidate CI passed 128 adapter tests and scoped engine checks; see [feature evidence](../docs/codex-adapter/feature-validation-2026-09-21.md). Final main CI and release artifacts require their own verification.

## Compatibility boundaries

- Custom-role selection depends on the Codex host. Where unavailable, required work is delegated to real child agents that load the complete source role. No simulated team is substituted.
- Role profiles omit model/effort overrides by default, so host spawn defaults and then the parent model apply. Explicit configured overrides take precedence. Claude model tiers, tool restrictions, turn budgets and memory flags are preserved as metadata/instructions, with documented host differences.
- Notification events and the original status-line UI have no identical mapping. Native Windows registration is not validated.
- Automatic checks require trusted hooks. External editors and arbitrary shell writes are not universally covered by file-edit events.
- No complete Godot, Unity or Unreal game has been certified through this adapter yet.

See [runtime behavior](../docs/codex-adapter/runtime.md), [hook coverage](../docs/codex-adapter/hooks.md) and [test evidence](../docs/codex-adapter/validation.md) before relying on a particular mechanism.

## Updating and contributing

Keep original source files as the workflow authority. After deliberate source or runtime-contract changes, run `python3 tools/ccgs_codex.py generate` and the verification commands above. Do not edit generated entries by hand. Include the Codex version, operating system, workflow, expected behavior and a minimal reproduction in reports; omit credentials and private game content.

This repository uses a snapshot of the named upstream revision. It does not claim an official upstream fork relationship or a shared Git commit history. Future upstream changes should be reviewed and tested before adoption.

## Credits and license

Original studio: **Donchitos**, [Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios). Codex adaptation maintained by **Bruuuucy101**.

The original [MIT license](../LICENSE) and copyright notice are retained. The added Codex adaptation is also offered under MIT; see [adaptation license](../LICENSE-CODEX). Original sponsorship links refer to the upstream creator. No affiliation or endorsement is implied.

### Optional GitHub board

Use `ccgs-board-sync snapshot` for local mapped story data, then explicit project
setup and `sync --dry` for a remote preview. Only `--write` applies changes.
[Setup, optional dependencies and recovery](../docs/codex-adapter/board-sync.md)
describe gh access and contract tests; live GitHub acceptance remains unverified.

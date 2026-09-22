# Production Integration Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accurate, CI-gated v0.3.0-beta release of the tested production integrations.

**Architecture:** Extend the existing release job and current entry documentation using completed feature reports. Controller publishes and verifies exact committed trees and release archives after the whole-branch review.

**Tech Stack:** Existing Markdown, GitHub Actions, Python verification and optional feature runtimes.

**Spec:** `docs/superpowers/specs/2026-09-22-production-release.md`

## Global Constraints

- Version/tag is `v0.3.0-beta`, archive `Codex-Game-Studio-v0.3.0-beta.zip` with prefix `Codex-Game-Studio/`, checksum file `SHA256SUMS.txt`. Existing releases/tags remain unchanged.
- Preserve every original and v0.2.0-beta role/workflow identity and the byte-identical 417-file original lock. The four new workflow identities are board-sync, npc-voice, creative-tools and asset-produce: expected final inventory 78 workflows and 57 roles. Derive other counts from actual final files.
- Local unit, actual HTTP fixtures, file/race/crash tests, model/native runtime, sampled workflow behavior, cloud CI, paid provider/account, creative review and engine import are separate evidence. Report source revision, actual commands/results and explicit unavailable evidence. A successful fixture is not a live-account or artistic-quality claim.
- Release only the exact reviewed commit after its required CI jobs pass. Keep PR publication disabled, public-repository/main-only conditions, contents-write scoped to release job, and existing-tag/release protection. An inaccessible API is not evidence that a release is absent.
- Preserve original attribution/license and qualified third-party model/runtime rights. No credentials, personal filesystem paths, weights, build output, private job records, runtime caches or SDD scratch enter published source or archive.

## Review Focus

- A README command copied verbatim must use an implemented route and documented optional dependencies; exercise no-write examples in clean fixtures.
- Current counts and issue dispositions must not rewrite historical release claims; compare exact role/workflow sets and dated evidence sections.
- A failed always-required optional feature job must block release; inspect the actual final needs graph and PR/main conditions.
- Existing tags/releases and transient API failures must preserve prior artifacts; retain the current list-endpoint idempotency behavior.
- Release ZIP bytes/modes must correspond to the exact tested git tree and exclude private/runtime files; use actual tree/archive comparisons, not filenames alone.

### Task 1: Version, evidence and release documentation

**Files:** Modify `RELEASE_NOTES.md`, `.github/workflows/codex-adapter.yml`, `README.md`, `README-CODEX.zh-CN.md`, `UPGRADING.md`, `docs/codex-adapter/{validation,capabilities,operating-guide,upstream-issues-2026-09-21}.md` as needed for actual current statements. Create `docs/codex-adapter/production-validation-2026-09-22.md`. Refresh exact reviewed patch entries and generated manifests only for changed canonical sources.

**Interfaces:** Consume completed reports in each `2026-09-21-{board-sync,asset-production,npc-voice,local-asset-tools,creative-production-workflows}` SDD workspace and controller evidence in `../round3-evidence/` and `../round3-behavior/`. Produce portable evidence/quickstart docs and an exact versioned release workflow. Do not include private absolute paths or raw provider evidence. Controller owns all external publication and final artifact verification.

- [ ] Read binding spec and actual completed feature reports/acceptance receipts supplied at dispatch. If an implementation or required native gate is missing, report it instead of advertising success. Inspect actual CLI help and current workflow/catalog identity sets.
- [ ] Update release notes and current quickstarts with concrete new behavior, dependencies, safe preview/write examples and remaining limits. Keep all original engines, roles, full/lean/solo modes and historical release evidence discoverable. Include ordinary recovery steps and distinguish retained partial publication from successful collection.
- [ ] Update issue dispositions for #82/#23/#14/#40 with delivered scope and actual evidence, preserving historical v0.1.1/v0.2.0 sections. Do not claim upstream closure, broad live provider support, complete GUI integration or engine import from fixture tests.
- [ ] Write the production validation guide from actual reports, computing current counts and citing real source identities/test commands. Distinguish the model/native startup probes from tests of final shipped wrappers and distinguish native MCP visibility from successful connection.
- [ ] Change existing release version/archive/title occurrences from v0.2.0-beta to v0.3.0-beta only in the current release job. Preserve repository/main/PR guards, existing tag/release checks and failure semantics. Extend needs to all actual always-required feature jobs; any separately manual model test must have its real acceptance evidence recorded by controller before release.
- [ ] Validate no-write quickstart commands in isolated fixtures; parse the final workflow using the existing board PyYAML runtime and verify its release dependency graph. Compare exact final identities with original lock and v0.2.0 baseline, run generation and strict provenance plus full core adapter tests and diff hygiene. Reuse unchanged feature test evidence at the same source rather than rerunning every native suite without a reason. Do not add prose-mirroring tests for documentation edits.
- [ ] Self-review and commit owned files. Write `task-1-report.md` with exact changed scope, commands/output, release prerequisites and unavailable external evidence. No children, global changes, paid calls or external publication. Controller then runs one whole-branch review, its bounded fix process, final candidate CI, authorized merge and release verification.

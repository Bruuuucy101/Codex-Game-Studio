# Feature Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accurate v0.2.0-beta documentation and CI-gated release metadata after all feature phases pass.

**Architecture:** Existing release workflow packages the exact tested Git commit; documentation links the per-feature evidence and preserves historical records.

**Tech Stack:** Markdown, GitHub Actions, existing Python verification and feature runtimes.

**Spec:** `docs/superpowers/specs/2026-09-21-feature-release.md`

## Global Constraints

- Version/tag is `v0.2.0-beta`, archive `Codex-Game-Studio-v0.2.0-beta.zip` with prefix `Codex-Game-Studio/`, checksum file `SHA256SUMS.txt`. Existing releases/tags remain unchanged.
- Complete selected source feature inventory is 75 workflows and 57 roles: original 73/49 plus setup-tool, board-sync, two web specialists, game-pipeline-developer and five libGDX specialists. Assert identities, not counts alone; derive all other counts from actual files. Original 417-file lock bytes stay unchanged.
- Local unit, real filesystem, sampled agent behavior, browser/headless-engine, CI and release artifact verification are separate evidence. Report actual environment/commands/source hashes and explicit unverified platforms/providers. Do not turn skipped or contract-only tests into live integration claims.
- GitHub release must wait for Python 3.10/3.12, web matrix, board contract and libGDX headless/build jobs for the actual published revision. A PR/feature branch never publishes a release. Repeated release execution is idempotent and does not replace an existing tag/asset.
- Preserve original LICENSE/attribution. Document third-party wrapper/dependency licensing and source without presenting external dependencies as relicensed MIT code. No personal filesystem paths, secrets, runtime caches, browser profiles, generated build output or SDD scratch in published source.

## Review Focus

- Current inventory language must not overwrite historical evidence; inspect dated sections and source-derived counts.
- Readme quickstart must use actually implemented CLI and exact dependencies; exercise command help/preview in clean fixtures.
- A failing optional-feature job must block release; validate complete needs graph and PR/main conditions.
- Existing release or transient API failure must not overwrite old assets; preserve idempotent behavior and distinguish missing from inaccessible state where necessary.
- Artifact manifests must retain binary wrapper bytes/mode and exclude caches/private artifacts; controller verifies full committed and remote trees.

---

### Task 1: Release metadata, issue dispositions and evidence guide

**Files:** Modify `RELEASE_NOTES.md`, `.github/workflows/codex-adapter.yml`, `README.md`, `README-CODEX.zh-CN.md`, `docs/codex-adapter/{validation,upstream-issues-2026-09-21,operating-guide}.md`, `UPGRADING.md` if upgrade steps need new optional dependency guidance; other current inventory/source references only when materially stale. Add a concise `docs/codex-adapter/feature-validation-2026-09-21.md` for actual new evidence. Refresh provenance/generated files only if canonical baseline docs change.

**Interfaces:**
- Consume completed task reports and actual CI/behavior receipts provided by controller. No invented pass counts or placeholders; compute current inventories, quote actual commands/results and label unavailable evidence explicitly.
- Produce exact v0.2.0-beta release action and coherent entry docs. Controller alone publishes candidate/main/release and verifies artifacts; this worker makes no external writes.

- [ ] Read spec and controller-provided completed task/acceptance reports. Inspect actual CLI help, generated catalog and CI dependency graph. Confirm all selected feature gates are complete; report any missing implementation rather than advertise it.
- [ ] Update release notes with concrete new behavior, examples and limitations, attribution and upstream issue links. Rewrite current 34-issue dispositions and counts for delivered features, retain other issue reasoning and historical v0.1.1 observations. Do not claim upstream maintainers closed issues.
- [ ] Update both quickstarts with setup-tool, scaffold-web, scaffold-libgdx and optional board snapshot/setup/sync usage, exact runtime prerequisites and safe preview/write semantics. Clearly state no live Projects account test and no mobile/Kotlin/WebGPU/provider execution unless actual receipt proves it. Keep full/lean/solo and all original capabilities discoverable.
- [ ] Update the release workflow's exact version/archive/title/notes and all needs dependencies; preserve public repository/main-only/write permissions and existing-tag protection. Do not publish from PR. Add focused configuration/packaging assertions only where they verify a real release invariant; no tests that merely repeat prose.
- [ ] Validate documentation links/CLI examples, exact source identity sets, provenance/generation and diff hygiene. Run full adapter suite and affected metadata/release checks; do not redundantly rerun unchanged browser/Gradle suites already verified at the same source. Self-review and commit with Task 1 reference; full report with exact observed tests and limitations. No subagents or external publication.

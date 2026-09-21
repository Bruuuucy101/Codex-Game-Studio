# Web Engines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phaser 3 and Three.js onboarding, specialist support and actually tested game scaffolds.

**Architecture:** Canonical studio sources own role/workflow behavior; generated Codex entries mirror them. A small stdlib copier installs standalone Vite templates with pure simulation and thin engine integration.

**Tech Stack:** Python 3.10+ stdlib; TypeScript; Phaser 3; Three.js; Vite; Vitest; Playwright.

**Spec:** `docs/superpowers/specs/2026-09-21-web-engines.md`

## Global Constraints

- Preserve the 417-file baseline lock byte-for-byte (SHA256 `fb68f5ff2fd503611db210ee6c84e7820865778b4da4275bf5447667a2a72afa`); record every modified baseline file's exact reviewed hash and issue provenance. Never enroll new files into that original lock.
- Preserve all 73 original workflow identities and all 49 original role identities and full role bodies except deliberate documented extensions; regenerate Codex entry points from canonical `.claude/` sources.
- Engine IDs are `phaser` and `threejs`; specialists are `phaser-specialist` and `threejs-specialist`. Aliases `phaser3`, `three` and `three.js` resolve to those IDs.
- Tested baseline candidates are Phaser `3.90.0`, Three.js `0.186.0` (r186), `@types/three` `0.186.0`, Vite `7.3.6`, TypeScript `5.9.3`, Vitest `4.1.11`, Playwright `1.58.2`, Node `22.14.0`. Exact direct versions and committed lockfiles are required. Installed project pins take precedence; do not migrate Phaser 3 to Phaser 4 silently.
- Source presence, deterministic Python tests, sampled agent behavior, browser integration and native hardware testing are distinct evidence. Record actual commands and versions; do not claim mobile/Safari/WebGPU or all engine parity from Chromium.
- No telemetry, external game assets, billable services, global trust/configuration edits or automatic dependency installation by the scaffold helper.

## Review Focus

- Existing mixed engine/language paths must retain original behavior; Task 1 tests baseline identities and routing branches.
- A cloned studio containing template source must not look like a configured game; Task 1 tests exclusion and workflow policy.
- Reused scenes or lost browser focus must not duplicate listeners or leave movement stuck; Task 2 browser tests repeated reset and blur.
- Late file collisions and symlink ancestors must cause no existing-data mutation; Task 2 filesystem fixtures validate preflight and hashes.
- A production build must use the same assets and package versions as development; Task 2 clean-copy lock/build/browser acceptance proves this.

---

### Task 1: Complete canonical web-engine workflow support

**Files:**
- Create `.claude/agents/phaser-specialist.md`, `.claude/agents/threejs-specialist.md`, `.claude/docs/web-game-development.md`, `docs/engine-reference/phaser/` and `docs/engine-reference/threejs/` version/lifecycle/testing/reference documents, matching behavioral role specs, `tests/codex_adapter/test_web_engines.py`.
- Modify `.claude/skills/{setup-engine,brainstorm,dev-story,code-review,test-setup,test-helpers,smoke-check,project-stage-detect}/SKILL.md` only where engine selection/routing/testing needs extension; preserve every existing branch.
- Modify `CLAUDE.md`, `.claude/docs/{agent-roster,agent-coordination-map,quick-start,coding-standards}.md`, actual closed-choice engine templates, `docs/engine-reference/README.md`, behavioral catalog/specs, README-CODEX/current inventory docs, `tests/codex_adapter/test_catalog.py`, `.github/workflows/codex-adapter.yml`, provenance ledger and generated entries as required.

**Interfaces:**
- Consumes the existing dynamic catalog/generator and pinned original lock; current inventory starts at 73 skills/49 roles.
- Produces canonical `phaser`/`threejs` engine setup, full specialist roles (total 51), exact references, complete review/test routing and docs for the Task 2 scaffold interface `scaffold-web ENGINE --target PATH [--write]` under `templates/web/{engine}`. Until Task 2 lands, describe scaffolds as forthcoming in the staged implementation, not already runtime verified.

- [ ] Read the spec and `../round2-research/web-engines.md`; inspect relevant original role/workflow patterns and applicable rules. Read source references only as needed, not the whole repository.
- [ ] Add failing meaningful inventory/routing/source-contract tests: original identities from the baseline lock remain a subset; expected new role identities are exact; canonical and generated bodies match; all routing IDs exist; Phaser 3 and Three r186 remain distinct; existing Godot language modes and Unity/Unreal routes survive. Run focused tests and retain failing evidence.
- [ ] Write full roles following existing structure and restrictions: lifecycle/resource ownership/version consultation, domain expertise, collaboration, defer boundaries and bounded turn metadata; no fictional helper agents or implicit WebSearch permission. Add engine references with official dated URLs; specifically verify Three r186 versus unreleased r187 and explicit owned resource disposal.
- [ ] Extend setup selection/aliases, actual technical-preferences routing, onboarding recommendation and all relevant implementation/review/test/smoke branches. New language code routes to its specialist; shader technical-artist consultation and UI boundary are explicit. Preserve full/lean/solo and original role hierarchy. Detect actual web sources without counting installed templates/node_modules. Correct nearby verified licensing/platform misinformation without unrelated rewrites.
- [ ] Add behavioral specs with domain/version/wrong-engine/defer and lifecycle/trust cases; update catalogs and current docs without rewriting historical evidence. Generalize original-identity preservation tests and CI checks instead of merely increasing hardcoded counts. If generator wording calls newly authored roles original upstream roles, make wording source-accurate while preserving all bodies and metadata.
- [ ] Record baseline file patch hashes/rationale/issue links, regenerate, run focused tests then full `python3 -m unittest discover -s tests/codex_adapter -v`, `python3 tools/ccgs_codex.py check --strict-upstream`, `git diff --check`. Record exact results; no assertion of browser tests yet.
- [ ] Self-review and commit this task with conventional commit and Task 1 reference. Report files/commits/tests/remaining Task 2 obligations to the controller, do not spawn reviewers or other agents.

### Task 2: Safe scaffold command and real browser acceptance

**Files:**
- Create `tools/ccgs/scaffold.py`, `templates/web/phaser/`, `templates/web/threejs/`, `tests/codex_adapter/test_scaffold.py`.
- Modify `tools/ccgs/cli.py`, relevant setup/reference/README/validation documents, `.github/workflows/codex-adapter.yml`, `.gitignore` and provenance/generated artifacts only where required by this feature.

**Interfaces:**
- Consumes canonical Task 1 engine IDs, specialist routing and pins. Produces `scaffold-web ENGINE --target PATH [--write]` JSON manifest/copy result with clear nonzero errors; default is no-write. Templates are standalone game projects and do not alter the adapter repository's configured project stage.
- Each package exposes `dev`, `typecheck`, `test`, `build`, `preview`, `test:browser`. Vitest includes `tests/web-unit/**/*_test.ts`; Playwright uses `tests/browser` and production preview on loopback with strict port and owned process. Minimal source is `src/core/step.ts`, `src/gameplay/game.ts`, `src/scenes/`, `src/ui/`, `src/main.ts`, `src/styles.css`, `assets/data/game.json` plus configs/locks/instructions. Do not copy a root README.md or .gitignore over an existing studio.

- [ ] Read the spec and same research report; inspect CLI conventions and Task 1 outputs. Add failing copier tests for dry-run, exact manifest/hash equality, unknown engine, traversal, protected metadata, spaces, all collision positions, symlink source/destination/ancestor, repeat invocation and no partial damage. Prefer a narrow explicit manifest over recursive glob copying; enumerate exactly shipped template files.
- [ ] Implement stdlib copier and CLI integration. Reject malformed paths before resolution, protect `.git`, `.codex`, `.claude`, `.agents` targets, preflight before writes, never overwrite, never run npm/network. Use bounded straightforward functions and recover partial newly created files on failure without deleting pre-existing directories/files.
- [ ] Build the two small collect games using exact dependencies and committed npm lockfiles, generated primitive art and external config. Pure deterministic fixed-step simulation owns bounds/normalized movement/collection/reset. Thin engine/input adapters own lifecycle and render updates; no ECS/React/network/backend scope. Add unit tests first; no production test mutation hook.
- [ ] Add browser integration tests with actual keyboard/pointer interaction, visible game changes, score/reset twice, focus-loss clearing, resize, page/console errors, and actual Three WebGL2. A strictly test-build-only snapshot/advance hook may aid deterministic observations, but at least one meaningful full interaction uses actual input. Capture screenshots for visual inspection.
- [ ] Copy exact templates into clean fixtures outside tracked source. Run actual npm ci, typecheck, unit, production build, matching Chromium install and Playwright. Pin output versions/checksums and record evidence. Fix actual failures; do not label mocked screenshots or skipped tests successful. Runtime downloads stay task-local or standard tool cache; no global machine configuration changes.
- [ ] Add separate web CI matrix jobs and make release job depend on all Python/web jobs. Retain all prior CI/release safeguards. Keep base Python adapter tests dependency-free. Update docs with actual commands and tested limitations; stage flags cannot claim engine run when only source checks passed.
- [ ] Refresh reviewed patch hashes and generated files; run focused tests, full adapter suite, strict provenance and diff check. Self-review, commit with Task 2 reference and write full acceptance report outside tracked output. Do not spawn subagents or publish; controller owns independent review and publication.

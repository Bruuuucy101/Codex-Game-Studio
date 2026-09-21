# Codex adapter validation

Prior local acceptance: **v0.1.1-beta, 2026-09-21**. Original baseline: `984023ddac0d5e27624f2baacde6105e45de375f`. This report separates file integrity, deterministic checks, real Git fixtures and sampled model behavior. None certifies full runtime equivalence or actual game-engine readiness. The historical v0.1.0 evidence is retained below with its original date and scope.

| Evidence layer | Prior v0.1.1 observed result | Limit |
|---|---|---|
| Source integrity | All 417 baseline paths retained; 407 match original SHA256 and 10 match explicit reviewed patches; original lock unchanged | Reviewed corrections deliberately differ from upstream bytes |
| Capability inventory | 73 skills, 49 roles, 11 rules, 12 hook scripts, 40 recursive templates, 126 behavior-framework Markdown files retained | Inventory is not workflow execution |
| Generated integrity | 124 generated outputs pass integrity checks; all 49 original role bodies retained | Does not prove native role selection by every host |
| Deterministic adapter tests | 73 passing tests, covering generator/CLI/hooks, provenance, ADR parsing/pagination/freshness and workflow contracts | Workflow text assertions do not establish model adherence |
| Git update fixtures | Six actual local Git scenarios pass, described below | No remote update or real game customization is certified |
| Fresh-agent samples | Three scenarios on isolated copies of adapter commit `aff4ad7`, described below | Explicit entry loading; not native discovery, broad reliability or live-hook certification |
| Publication | Checked separately through the repository's Actions and release records | Local evidence does not claim CI or publication success |

Strict verification accepts only the original bytes or exact reviewed hashes, including validation of all patch records. `check --pristine-upstream` intentionally reports the 10 changed original files in this release. See [source maintenance](source-maintenance.md) and the [34-issue audit](upstream-issues-2026-09-21.md). Original lock SHA256: `fb68f5ff2fd503611db210ee6c84e7820865778b4da4275bf5447667a2a72afa`.

```sh
python3 tools/ccgs_codex.py check --strict-upstream
python3 -m unittest discover -s tests/codex_adapter -v
python3 tools/ccgs_codex.py doctor
```

## Current regression and Git evidence

New deterministic checks were observed failing before their respective fixes, then passing. They cover malformed or unsafe patch ledgers, exact source hashes, large single-line ADR sections, fenced fake status/headings, numbered/nested sections, ambiguous/missing status, complete bounded reconstruction, changed-file detection and corrected workflow ordering. An independent task review reproduced a fence-depth bug where a quoted marker inside a top-level code fence exposed a fake Accepted status; the depth-aware correction and regression now pass. Earlier phase reviews completed without remaining scoped findings; whole-branch release review is a separate acceptance step.

Six disposable local Git repositories exercised: shared/unrelated history with non-overlapping customization (2), shared/unrelated history with overlapping edits and explicit conflict resolution (2), ordinary fast-forward update (1), and divergent merge refusal/conflict/abort (1). The selective updates preserved customized source and untouched adapter/configuration sentinels. Failed `git apply --check` left files unchanged; three-way conflicts required actual resolution or restoration. These validate the documented command paths, not arbitrary conflict-resolution correctness, archive recovery, or network publication.

## Current fresh-agent observations

### Denied hotfix implementation

The user authorized investigation and the local hotfix branch/record, but explicitly refused implementation, merge and deployment. The agent diagnosed the negative-health issue and stopped at Phase 4a with BLOCKED status. Independent before/after file hashes showed only the authorized hotfix investigation record changed. Code and tests remained unchanged. No expert verdict, implementation, commit, merge or deployment was fabricated.

### Stale story summary and large current ADR

The story embedded obsolete speed 8 guidance and a stale per-ADR SHA256; its current acceptance criteria and current Accepted ADR required speed 12. The current ADR contained 420,571 characters, including a 420,000-character single-line historical Context section. The agent queried metadata, detected the hash mismatch, then retrieved 458 characters of relevant Decision, Implementation Guidelines, Engine Compatibility, ADR Dependencies and Amendments using `--expected-sha256` and an 8,000-character page limit. There were no missing sections or further pages. It did not return the historical Context body to model context.

The agent reconciled the story summary and source hash, changed JSON movementSpeed from 5 to 12, preserved schemaVersion 1, and passed actual JSON/type/exact-byte/current-hash checks. It used the canonical Config/Data exception and did not simulate a programmer or reviewer. Sprint/session state recorded implementation in progress; story acceptance remained unclosed with separate review and story-done still required. No engine execution was claimed.

### Missing runnable-demo prerequisites

The only original story covered two days of movement logic; the project entry, launch scene, player/input wiring and game tests were absent. In explicit solo review mode, the coordinator identified these gaps and scheduled setup/readiness (0.25 day), existing logic (2 days), scene/player/input integration (0.75 day) and actual integration/smoke/closure evidence (1 day). Four days of planned work leave the milestone's one-day buffer intact. Dependencies are ordered, ownership and acceptance are explicit, and unresolved startup/readiness blocks dependent work and triggers re-planning. The estimates are provisional and unvalidated by prior velocity.

Independent inspection confirmed the plan says the demo is currently not runnable, the existing QA plan is only requirements, new prerequisite stories need specification/readiness checks, and no producer or QA approval is claimed. Only the authorized sprint plan and status files changed. No scene, implementation or game-test result was created. This demonstrates observed prerequisite detection and planning, not estimate accuracy or a runnable game.

### Controller verification

Before/after SHA256 maps for all three fixtures confirmed no adapter-source changes, no denied hotfix code/test edits, exact movementSpeed 12 and schemaVersion 1 without story closure, and planning-only sprint writes with the scene still absent. All concrete file invariants passed. The controller separately inspected both implementation and sprint reports plus the complete sprint plan. These samples supplement the 73 passing deterministic adapter tests and six independently exercised Git update fixtures; they do not replace broader workflow or real-engine acceptance.

## Remaining acceptance work

Observe trusted automatic lifecycle/hooks in the target host; validate native custom-role selection where supported; run a complete feature with real engine tests, independent review, closure and stage QA. Expand the retained behavior framework across workflows and modes. Default model inheritance follows host spawn defaults then parent; explicit overrides can constrain models. No time/token savings, all-role coverage, Linux/native Windows support or engine certification follows from these checks.

---

# Historical v0.1.0-beta validation

Date: 2026-09-18. Baseline: `984023ddac0d5e27624f2baacde6105e45de375f`.

The delivery preserves the full upstream source surface and implements Codex entry points and compatibility mechanisms. It is not a certification of identical behavior across all workflows, models, platforms or engines. A configured hook is not proof of a trusted, executed hook.

## Evidence layers

| Layer | Observed result | What it does not prove |
|---|---|---|
| Source integrity | All 417 original tracked files match baseline SHA256; strict check passes | Original source correctness or runtime equivalence |
| Inventory | 73 skills, 49 roles, 11 rules, 12 scripts, 40 recursive template files, 126 testing-framework Markdown files | Every workflow was executed |
| Generated entry points | 73 full-source skill routes and 49 full-body role definitions; generation and integrity checks pass | Model adherence in every task |
| Syntax | All 49 role TOML files and project config parse using Python `tomllib` | Native role selection in this installed CLI |
| Deterministic tests | 34 tests pass: 12 catalog/generator, 5 CLI, 17 hook tests | Live host trust or game-engine playtests |
| Native skill discovery | Installed Codex diagnostic context contains all 73 `ccgs-*` skills; a model session confirms `ccgs-help` is discovered | Automatic execution of all 73 workflows |
| Native custom-role selection | Not exposed in this CLI test session | Do not report native custom-role loading as passed |
| Real role fallback | Actual CLI spawn/wait of one child; it loaded the composed technical-director role and reported its source and architecture responsibility | All 49 roles or complex team hierarchies were exercised |
| Sampled workflow behavior | Three isolated scenarios observed as described below | Statistical reliability or full scenario coverage |
| Live hooks | Registration and direct bridge invocation tested; desktop project/hook trust not activated by this work | Automatic events are firing in the user's desktop task |
| Engines and operating systems | macOS bridge/CLI tests; no actual engine build | Godot/Unity/Unreal production readiness, Linux or native Windows support |

## Reproduction

```sh
python3 tools/ccgs_codex.py check --strict-upstream
python3 -m unittest discover -s tests/codex_adapter -v
python3 tools/ccgs_codex.py doctor
```

Host: macOS, Python 3.10, Git and Bash available; jq absent in the default environment. An explicit minimal-PATH test also confirms the original no-jq validator rejects malformed JSON at a Unicode filename. TOML parsing additionally used the locally bundled Python with `tomllib`; the adapter itself needs only Python 3.10 and the standard library.

Codex CLI version: 0.150.1. A default-model smoke test failed with an explicit server response that `gpt-6-astra` needs a newer Codex. A one-run `gpt-5.5` override with low effort, ephemeral execution and read-only sandbox succeeded. Default user configuration was not changed. Startup warned about truncating some lengthy skill descriptions from the installed environment; entry discovery does not replace reading each full skill body.

## Historical sampled agent behavior

These scenarios used fresh application child agents, explicitly instructed to consume the generated skill entry, runtime contract and original source in separate disposable project copies. They were not native automatic skill-selection tests. Changes occurred only in those copies, not in the delivered studio. The memory/symlink/runtime-input fixes later changed adapter machinery, not the original workflows exercised here.

1. **Missing architecture prerequisite — dev-story.** A Config/Data story referenced a nonexistent governing ADR. The worker stopped at Phase 2, wrote BLOCKED session state and did not spawn a programmer. `assets/data/player.json` remained `{"speed": 5}`. Missing control manifest was reported as the original WARN. This verifies observed prerequisite refusal rather than a fabricated design.
2. **Actual implementation — dev-story.** A Config/Data story had a current registry, accepted ADR, matching manifest, documented schema and no dependencies. The worker changed `moveSpeed` from 5 to 8 and preserved `schemaVersion: 1`. It ran actual JSON, type and byte-change checks, wrote smoke evidence, updated story timestamp/sprint/session state, and kept the story unclosed. The original Config/Data exception correctly skipped programmer spawning. Baseline asset SHA256: `bd62de878031b7155172829961c5082077b71baaba20bf5e365783cae9997150`; final: `694950dd1c40c2615b8b4a0adfe1b9fc072fead6ab1c77693dac69d33b07f9aa`.
3. **Missing test evidence — story-done.** A Logic story in solo review mode had implementation but no required unit test or alternate passing evidence. The worker reported BLOCKED, 1/1 criteria UNTESTED and the additional tuning mismatch against current requirements. The story remained In Progress; no closure/sprint/session edits occurred. Solo mode skipped its original optional review gates, not the mandatory Logic evidence requirement.

The separate **native CLI delegation test** used the actual spawn tool and waited for a child (session identifier omitted from the public report). The child loaded `python3 tools/ccgs_codex.py role technical-director` and identified `.claude/agents/technical-director.md` and its architecture/ADR responsibility. This is evidence of a real loaded-role handoff, not a simulated team and not proof of a native custom-role-type selector.

Selected machine-readable outcomes and immutable fixture hashes are in [evidence.json](evidence.json). Full diagnostic prompts and private host configuration were deliberately not packaged.

## Independent review and regression evidence

An independent read-only review covered hook normalization and then the generator, CLI, runtime contract and generated entries. It found and reproduced:

- Lost nested asset/skill coverage and Unicode paths under the original no-jq fallback. Three failing regressions were added; the bridge fixes now pass all 17 hook tests.
- Generated-path symlinks could redirect writes. Output files, parent directories and the manifest now undergo a preflight check rejecting redirected destinations before any writes. Regression cases include an internal target, an external parent and a linked manifest.
- Missing `runtime.md` silently generated incomplete roles. This is now a hard error.
- Existing original role memory was not loaded by the new continuation mapping. The runtime and all generated roles now explicitly load original role memory first, then the project-local Codex continuation.

The latter fixes were preceded by five observed failing assertions (four new test cases plus a full-role memory assertion); the catalog suite passed after fixes. The independent reviewer rechecked all three findings and reported no remaining actionable issues in the affected scope, with all 12 catalog tests, 5 CLI tests and strict upstream checks passing. Generated notification inventory also now explicitly says there is no identical native event. Review conclusions are scoped to the inspected changes; they are not a security audit of upstream or a guarantee of future model behavior.

## Remaining acceptance work

Open this directory as the actual Codex project, review/trust its hooks, and observe live lifecycle and validation events. Select the real engine/version and run one complete feature through implementation, passing tests, independent review, closure and stage QA. Expand the original skill-testing framework across the desired workflows and full/lean/solo modes. Native Windows registration, all-engine behavior, complex nested teams, hard role-policy equivalence, notification equivalence and user-scoped memory remain unverified or documented host differences.

## Web-engine Task 1 extension — 2026-09-21

Canonical workflow support adds phaser-specialist and threejs-specialist while
preserving the original lock and 73 workflow/49 role identity sets. Current
inventory is 51 roles. Source-contract tests cover identity preservation,
canonical/generated bodies, routing targets and reference/spec resolution.
These are deterministic structural checks, not executed behavioral scenarios.
On Python 3.10.0, `python3 -m unittest discover -s tests/codex_adapter -v`
passed 77 tests after regeneration. `check --strict-upstream` passed; 417 baseline
paths remain (382 original hashes, 35 reviewed hashes), and the original lock
SHA256 above is unchanged. The generator produced 126 files; 51 role profiles
and project config parsed with the local pip-vendored tomli. `git diff --check`
passed. Python 3.12 CI and remote CI execution were not run locally.

Scaffold implementation, package installation, typecheck/unit/build/browser runs
and screenshot acceptance are forthcoming in Task 2. New behavioral catalog
entries intentionally have blank execution fields. No browser, Safari, mobile,
WebGPU or native hardware verification is claimed by this phase. Earlier counts
and observed runs above retain their historical scope.

## Web scaffold implementation — 2026-09-21

The `scaffold-web` command now previews/copies explicit manifests for Phaser 3
and Three.js without npm, network access, overwrites or engine-state changes.
Its filesystem tests cover both exact byte/hash manifests, dry-run, aliases,
invalid/traversal/protected paths, all output collision positions, symlinks,
repeat invocation, existing studio files and rollback after a mid-write failure.

Exact game pins remain Phaser 3.90.0 and Three.js/@types/three 0.186.0. The
initial Vite 7.3.1/Vitest 4.1.9 candidate passed build/unit checks but npm audit
reported development-server advisories. The reviewed baseline was refreshed to
Vite 7.3.6 and Vitest 4.1.11; TypeScript 5.9.3 and Playwright 1.58.2 remain pinned.
The compatible transitive esbuild resolved to 0.28.2; final `npm audit --json`
reported zero vulnerabilities for both locks on this date. Lock generation used
task-local npm 11.6.2 after npm 10.9.2's initial dependency
resolver threw an internal `edgesOut` error. The resulting lockfiles install
with normal npm 10.9.2 on Node 22.14.0 using `npm ci`; no global npm change or
peer-dependency bypass is required.

The clean-fixture acceptance commands are `npm ci`, `npm run typecheck`,
`npm test`, `npm run build`, `npx playwright install chromium`, then
`npm run test:browser`. Fresh copies of both final templates passed all four install/type/unit/build
commands on Node 22.14.0/npm 10.9.2. After review fixes, each template passed
ten unit tests: five simulation, two modifier-input and three page-lifecycle tests.
Matching Chromium installation and discovery of four browser scenarios per
template succeeded; discovery did not execute them. Unit discovery is
`tests/web-unit/**/*_test.ts`; browser discovery is `tests/browser`. The engine
bundles currently trigger Vite's 500 kB chunk warning (approximately 1.21 MB
Phaser / 530 kB Three.js uncompressed JS); these are starter templates, not
optimized download budgets.

Browser acceptance remains **NOT VERIFIED locally**: downloaded Chromium 145
and its matching headless shell abort before page creation in this macOS host's
application registration path. Type/unit/build checks and Playwright discovery
are separate evidence and do not prove canvas output. The release-blocking Linux
web CI matrix runs real keyboard/pointer, two collection/reset cycles, focus
clearing, resize, teardown and actual Three WebGL2 checks against owned production
preview. Additional scenarios exercise modifier transitions and explicit persisted
pagehide/pageshow suspension/restoration; the latter tests the event contract,
not the browser’s independent back/forward-cache eligibility decision. Final
pagehide/HMR still releases owned resources. It uploads screenshots/traces for
inspection, including failure artifacts.
Until that CI run and visual inspection are recorded, browser acceptance is open.
The full Python adapter suite passed 87 tests; strict provenance and generated
integrity checks passed with the original lock unchanged.
Safari, mobile, WebGPU, native GPU performance and behavioral-agent adherence
remain unverified. The historical Task 1 counts/results above are unchanged.

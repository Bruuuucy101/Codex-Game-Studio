# Codex adapter validation

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

## Sampled agent behavior

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

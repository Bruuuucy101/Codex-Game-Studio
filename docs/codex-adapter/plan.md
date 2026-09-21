# Complete CCGS Codex Adapter Implementation Plan

> Historical v0.1.0-beta migration record (2026-09-18). Its unchanged-source requirement and original observations describe that release. For v0.1.1-beta reviewed source corrections and current evidence, see [source maintenance](source-maintenance.md), [issue audit](upstream-issues-2026-09-21.md) and [validation](validation.md).

> For agentic workers: use superpowers:subagent-driven-development for the independent hook task and review. Preserve the full source contract in the spec.

Goal: carry the full upstream studio surface into a traceable Codex project.
Architecture: unchanged upstream files plus generated entry points, native role definitions, event bridge and validation.
Tech stack: Python 3.10+ standard library, unchanged Bash scripts, Codex project config, JSON and TOML.
Spec: docs/codex-adapter/design.md

## Global constraints

Keep all original tracked files unchanged. No global install, no publishing, no permission bypass. No claim of full runtime parity from counts alone. Source commit 984023ddac0d5e27624f2baacde6105e45de375f. Preserve all engines and review modes.

## Task 1: Source inventory, adapters and parity checker

Files: tools/ccgs_codex.py, tools/ccgs/{__init__,catalog,generate,cli}.py; tests/codex_adapter/test_catalog.py; .codex/upstream-lock.json; .codex/capabilities.json; .agents/skills/ccgs-*; .codex/agents/*.toml.

- [x] Write tests that deleting an original source, changing generated output and omitting an adapter fail verification; workflow full-source reads and embedded role bodies preserve content.
- [x] Run `python3 -m unittest discover -s tests/codex_adapter -p 'test_catalog.py' -v` and record missing implementation failures.
- [x] Implement `catalog(root: Path) -> dict`, `generate(root: Path) -> dict[path, text]`, `check(root: Path) -> list[str]`; source baseline stored with SHA256 digests, original headers and source references.
- [x] Generate all outputs, validate namespaced skills and TOML, run tests and document results.

## Task 2: Hook bridge (independent implementation owner)

Files owned exclusively by hook worker: tools/ccgs_hooks.py, tests/codex_adapter/test_hooks.py, docs/codex-adapter/hooks.md, .codex/hooks.json.
Interface: `python3 tools/ccgs_hooks.py EVENT` accepts official hook input JSON on stdin, resolves repository root from this file and runs unchanged `.claude/hooks/` scripts at that root; stdout is valid event-appropriate Codex JSON, exit 2 for blocking failures.

- [x] Read all 12 source scripts and current official hook event semantics.
- [x] Write and run failing real-script tests using temporary fixture roots, including a multi-file apply_patch and malformed payload.
- [x] Implement bridge plus registration, session and audit support, rule context, explicit notification limitations.
- [x] Re-run tests, provide exact evidence and separate host limitations. Do not change original scripts or global settings.

## Task 3: Runtime instructions and startup diagnostics

Files: AGENTS.md, docs/codex-adapter/runtime.md, README-CODEX.zh-CN.md, tools/ccgs/cli.py, tests/codex_adapter/test_cli.py, .codex/config.toml.

- [x] Document concrete translation of every original tool/metadata behavior. Keep authorization inherited from user and preserve required quality gates. Real subagents for required delegation; schedule waves within host limits and report a blocker when delegation is unavailable.
- [x] Test doctor/status/rules/role commands on temporary source fixtures; status works without state and reports actual state when present; doctor differentiates source drift and unverified runtime.
- [x] Implement commands using stdlib and no network or user config writes. Verify role source display and path-scoped rule selection.
- [x] Verify local CLI parses config and discovers skills where the available host permits.

## Task 4: Integration, behavioral evidence and delivery

Files: docs/codex-adapter/validation.md, docs/codex-adapter/capabilities.md, tests/codex_adapter/*; delivery zip outside repo.

- [x] Run all deterministic tests and strict original-source comparison to baseline.
- [x] Run bounded behavior scenarios with fresh agents, preserving evidence and identifying native-host versus prompted-context tests.
- [x] Request an independent code review, fix actionable issues with regression tests and re-review affected scope.
- [x] Record supported mechanisms, tested cases, and unverified platform/engine cases. Commit local changes and create archive without .git, caches or runtime logs.

Execution note: All implementation tasks are complete. Host/engine acceptance boundaries and exact evidence are recorded in validation.md; checked implementation tasks do not imply full runtime equivalence.

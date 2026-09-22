# Board Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optional previewable, recoverable GitHub Projects v2 projection from canonical local stories.

**Architecture:** Separate local snapshot/parser, GitHub transport/reconciliation and narrow CLI/workflow integration. Remote state is always rediscovered; stable markers establish ownership and apply checks snapshot freshness.

**Tech Stack:** Python 3.10+, optional PyYAML 6.0.3, authenticated gh GraphQL subprocess; unittest fixtures.

**Spec:** `docs/superpowers/specs/2026-09-21-board-sync.md`

## Global Constraints

- Preserve original baseline lock, prior source identities/features, reviewed patch provenance and generated entry consistency.
- New implementation is Python 3.10+; optional board dependency is `PyYAML==6.0.3` in `requirements-board.txt`. Core adapter commands and core tests remain stdlib-only; board tests run separately with this dependency installed.
- Actual transport uses argument-array `gh api --hostname github.com graphql --input -` with JSON stdin and `shell=False`. Never interpolate story data into shell or GraphQL query text. No credentials are collected or persisted.
- All board state is confined to `.ccgs-board/` (`board.config.json`, `state.json`, `mapping.json`, scoped lock); add this to ignore rules. Existing documents are never modified. Dry operations write no state.
- A stable identity marker is derived from explicit configured namespace plus canonical project-relative story path; title matching alone never adopts a card. Unmanaged cards, fields and options remain untouched.
- Every run re-reads remote state including all paginated fields, items and nested field values; local cache is a hint, never authority. Duplicate managed identities stop mutation with a conflict.
- Apply revalidates local inventory and raw source hashes, including sprint YAML, before external writes. Local concurrent runs use an owned lock. Lost-response create mutations are not blindly retried; reconcile remote state on rerun. Do not promise cross-host exactly-once behavior.

## Review Focus

- Story header Ready with YAML in_progress must export In Progress; parser tests pin actual canonical precedence.
- Existing field option IDs must survive extension; stateful remote fixture tests values of unrelated cards remain intact.
- A successful remote create with lost response must not duplicate on rerun; fake gh persists state before timeout.
- A changed local inventory between preview and apply must fail before any remote mutation; snapshot revalidation tests count all calls.
- Config symlinks, duplicate markers or epic filters must not target another project/document; path/ownership fixtures pin these cases.

---

### Task 1: Local canonical story snapshot

**Files:** Create `tools/ccgs/board_snapshot.py`, `requirements-board.txt`, `tests/board_sync/test_snapshot.py`, fixture helpers. Add lazy `board-sync snapshot` route to `tools/ccgs/cli.py`; document local snapshot format in `docs/codex-adapter/board-sync.md`.

**Interfaces:**
- `build_snapshot(root, epic=None) -> dict` and `validate_snapshot(root, snapshot) -> None` exported from board_snapshot. Snapshot includes schema version, selected epic, canonical inventory, source SHA256s, deterministic snapshot SHA256, story path/identity input/title/raw metadata/normalized fields/status source and warnings. No timestamps in digest and no writes.
- Namespace-based remote marker is Task 2's responsibility; snapshot identity input is canonical relative story path. Errors are ValueError subclasses with safe actionable messages. YAML import is lazy and required only when parsing an existing sprint YAML; absence of dependency gives install instructions. Unknown/duplicate metadata or invalid status never silently defaults.

- [ ] Read spec and `../round2-research/board-sync.md`; inspect actual create-stories/sprint-plan/sprint-status/dev-story formats. No document modifications are needed to fix precedence; implement the source-of-truth rule.
- [ ] Write failing parser tests for standard blockquote headers, Unicode/CRLF, fenced/body examples, all mappings, missing/duplicate/invalid fields, repeated numbers across epics and unsafe/symlink paths. Add actual YAML schema tests for in_progress and hyphen states, duplicate keys/references, malformed/aliased/oversized input and legacy out-of-scope references. Record focused failure.
- [ ] Implement bounded standard-library Markdown metadata parsing and optional strict SafeLoader subclass (reject duplicate keys/aliases/custom tags). Normalize according to exact spec, preserve source evidence, and reject ambiguous estimates. Use canonical root-relative safe paths; no runtime code execution or writes.
- [ ] Implement stable inventory/hash snapshot and revalidation, covering story/YAML edits, additions, removals and symlink substitution. Epic filter is one exact safe folder slug. Tests assert all original file hashes unchanged. CLI snapshot produces deterministic JSON without gh installed.
- [ ] Add optional dependency docs and separate test runner instructions. Run board tests in task-local venv with pinned PyYAML, full core adapter suite without requiring that venv dependency, strict provenance and diff check; self-review and commit. Report exported schema in report so Task 2 can consume it verbatim. No subagents or publication.

### Task 2: Real GitHub transport and recoverable sync workflow

**Files:** Create `tools/ccgs/board_github.py`, `tools/ccgs/board_sync.py`, `.claude/skills/board-sync/SKILL.md`, matching behavioral spec, `tests/board_sync/test_sync.py`, `tests/board_sync/fake_gh.py`. Extend CLI, board docs, skills-reference/catalog/current README/validation, .gitignore, CI, provenance/generated artifacts.

**Interfaces:**
- Consume Task 1 `build_snapshot` and `validate_snapshot`; exact final schema is in its report. Expose setup/sync commands specified in the design; `--dry` is explicit synonym for default no-write, mutually exclusive with `--write`.
- Config/state files reside only `.ccgs-board/`; config pins namespace and actual project owner/id/number/URL. Transport has small injectable executable boundary for fake gh while production uses gh argv and fixed github.com. Library injection is not an arbitrary executable CLI/config setting.

- [ ] Read fresh schema evidence in `../round3-research/board-schema-notes.md` and the downloaded official schema `../round3-research/github-schema-2026-09-21.graphql`. Explicitly query `archivedStates: [ARCHIVED, NOT_ARCHIVED]` because the API defaults to active items only. Archived managed cards must not be recreated/unarchived implicitly. Preflight the documented50option limit while preserving existing options; never drop options to make room. Keep complete GraphQL documents in inspectable constants or retain fixture request logs so the controller can validate every operation against the independently downloaded full schema.
- [ ] Read spec, Task 1 report, relevant GitHub official API documentation linked in research. Add stateful fake transport tests first for project resolution/setup, field/item/value pagination and single-select option preservation; record failing evidence. Keep query variables separate from query text and use exact current schema input fields.
- [ ] Implement gh JSON transport with safe diagnostics, bounded read retries, HTTP-success GraphQL error handling, pagination including nested values, user/organization project resolution and strict config validation. Do not print raw response/stderr that may contain secrets. Redacted remote items and inaccessible projects are explicit constraints.
- [ ] Implement dry setup/adoption/private creation and crash-safe setup recovery. Before creation write only an authorized owned intent record; after uncertain result reconcile actual owner project list and marker/evidence or report candidates without repeating create. Do not mutate an existing different config. Dry setup creates neither intent nor project.
- [ ] Implement deterministic diff/reconcile: stable namespace+path ownership marker in draft body, all current field options retained with IDs, new option refresh, exact managed card updates, zero-change rerun, duplicate-marker conflict, untouched unmanaged content. Deleted/renamed paths report stale only; do not add prune/archive scope. Epic sync never touches another epic.
- [ ] Implement apply lock with explicit stale-lock recovery guidance (never steal live lock), input inventory/hash revalidation before mutations, atomic owned state writes, partial/uncertain outcomes and final remote verification. Never retry a create blindly. Test write-before-timeout then rerun, partial field/card failures, remote drift, snapshot change, redacted items and auth failures through the actual CLI/fake gh subprocess.
- [ ] Add full optional board-sync skill with actual delegated tools-programmer handoff if Bash isn't allowed, no invented gh capability, preview/write semantics and no existing-doc edits. Register workflow/spec; preserve baseline and prior additions. Document setup/auth, state ownership, exact mappings, recovery and contract-versus-live evidence.
- [ ] Add separate CI board test job with requirements-board and make release depend on it plus all prior checks. Run complete board suite, full core suite, strict provenance, generation consistency and diff check. Self-review, commit and report commands/results/limitations. No actual user board mutation, subagents or publication; controller owns live capability assessment and review.

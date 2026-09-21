# Optional GitHub board projection — design

Implements upstream [#82](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/82). The user's delegated scope covers building and publishing this integration. It does not require creating an actual account board during development. Live GitHub Projects acceptance is separate from contract tests and remains unverified without a callable authenticated Projects API.

## Outcome

An opt-in `/board-sync` workflow previews or applies a GitHub Projects v2 view of `production/epics/*/story-*.md`. It creates draft project cards and four custom single-select fields, never repository issues/comments. Existing story, epic, index, plan, GDD and ADR documents are read-only. Other studio features work without gh or PyYAML.

## Global constraints

- Preserve original baseline lock, prior source identities/features, reviewed patch provenance and generated entry consistency.
- New implementation is Python 3.10+; optional board dependency is `PyYAML==6.0.3` in `requirements-board.txt`. Core adapter commands and core tests remain stdlib-only; board tests run separately with this dependency installed.
- Actual transport uses argument-array `gh api --hostname github.com graphql --input -` with JSON stdin and `shell=False`. Never interpolate story data into shell or GraphQL query text. No credentials are collected or persisted.
- All board state is confined to `.ccgs-board/` (`board.config.json`, `state.json`, `mapping.json`, scoped lock); add this to ignore rules. Existing documents are never modified. Dry operations write no state.
- A stable identity marker is derived from explicit configured namespace plus canonical project-relative story path; title matching alone never adopts a card. Unmanaged cards, fields and options remain untouched.
- Every run re-reads remote state including all paginated fields, items and nested field values; local cache is a hint, never authority. Duplicate managed identities stop mutation with a conflict.
- Apply revalidates local inventory and raw source hashes, including sprint YAML, before external writes. Local concurrent runs use an owned lock. Lost-response create mutations are not blindly retried; reconcile remote state on rerun. Do not promise cross-host exactly-once behavior.

## Source and mappings

Parse only standard header metadata before the first body H2, ignoring fenced examples and later Test Evidence Status. Required title/Status/Type/Estimate/Epic must be unambiguous and meaningful; malformed/duplicate/unknown values are actionable validation errors, not guessed Done/Ready. Preserve raw values and source provenance in preview.

`production/sprint-status.yaml`, when present, is canonical for matching story `file` entries; it overrides stale story-header status as original sprint-status requires. Support the actual `stories: [{file, status, ...}]` shape, validate duplicate keys/references, unsafe paths and malformed input. Stories outside the scanned epics are not silently exported; warn for legacy/out-of-scope references. Header status is fallback for stories absent from YAML. Both `in-progress` and the original dev-story's `in_progress` normalize correctly. A changed/added/removed story or YAML invalidates the snapshot. Bounded safe YAML loading rejects aliases/custom tags/duplicate keys and excessive input rather than evaluating arbitrary objects.

Fields: Stage = Backlog / Ready / In Progress / In Review / Blocked / Done / Deferred; Type = Logic / Integration / Visual / UI / Config (normalize Visual/Feel and Config/Data); Size = S/M/L; Epic = canonical epic folder slug, retaining human label in body. `In Review` is retained because the real sprint workflow uses it. XS/S→S, M→M, L/XL→L; positive finite hour estimates up to 4h→S, up to 16h→M, above 16h→L. Ambiguous days/ranges/placeholders fail with instructions to choose hours or t-shirt size. Explicit custom field type/name conflicts stop before writes.

## CLI and behavior

`python3 tools/ccgs_codex.py board-sync snapshot [--epic SLUG]` is local-only JSON, including inventory/hash, raw/normalized values and status source. `board-sync setup --owner OWNER --namespace NAMESPACE (--number N | --title TITLE) [--write|--dry]` previews/adopts an existing user/organization project or creates a private project and config only on write. Existing config is verified, not silently replaced with a different project. `board-sync sync [--epic SLUG] [--write|--dry]` defaults to dry preview, discovers actual remote differences, then optionally applies and verifies.

Config has schema version, host github.com, owner identity/type, project number/node ID, namespace and expected project URL. Validate every loaded field and safe local path; no arbitrary executable, query or hostname config. A setup interrupted after remote creation must reconcile by persisted operation evidence or report candidate projects for explicit adoption, not blindly create another. Dry setup has no local/remote mutations.

GitHub field option replacement must retain every existing option with its id/name/color/description, then add missing options and re-read IDs. Never erase unrelated option values. Fetch enough metadata to do so. GraphQL errors inside HTTP-success responses fail explicitly. Reads can retry bounded transient failures; mutations use reconcile-safe semantics, with explicit partial/uncertain result on failure. Token-looking data/raw request bodies are not printed.

Re-running an unchanged sync produces zero mutations. Remote title/body/field drift on managed cards is repaired; user-owned comments/other fields are not overwritten. Removed/renamed local paths produce stale-card reports; this release does not delete or archive any cards. Epic filtering cannot touch other epics, even for stale reporting. Final remote read verifies intended managed records and fields, not merely command exit codes.

## Verification and limits

Separate board suite covers real parser/CLI subprocess fixtures, canonical header+YAML precedence, all normalization states, Unicode/CRLF/fences/duplicate metadata, unsafe paths, hash/inventory invalidation and no document mutations. A stateful fake gh executable exercises real JSON/argv transport and GraphQL operation shapes, pagination, option retention, missing/wrong fields, no-op repeat, remote drift repair, duplicate identities, epic isolation, uncertain create then rerun adoption, partial failure recovery, authentication errors, GraphQL errors and stderr redaction. Actual GitHub schema references are recorded in documentation. These are transport/contract tests, not a live GitHub board test.

No installation or board writes happen automatically when opening the studio. CLI/API errors explain missing gh/project scope or optional PyYAML without disabling core adapter functionality. No unchanged-document write can be justified by the upstream proposal's claim that external side effects need no authorization; `--write` remains explicit.

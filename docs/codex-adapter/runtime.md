# Codex runtime contract for the complete upstream studio

The source workflow decides the work and acceptance criteria. This contract only translates host mechanisms. All original phase bodies, domain expertise, templates, engine variants, review modes and failure recovery rules remain authoritative. User instructions and host system/developer restrictions have precedence. Preserve existing user authorization instead of asking for the same write approval repeatedly; otherwise preserve the original decision/draft/approval stages.

## Loading and paths

Read `CLAUDE.md` and explicitly read its `@path` references. Read the selected complete `.claude/skills/<name>/SKILL.md`, relevant `.claude/docs/` references and templates. Load any original agent metadata `skills` before that role's work. Use file paths in the brief rather than copying every document into every child prompt, unless a source workflow explicitly requires an exact excerpt for a decision.

Original `.claude/...` paths stay valid and must NOT be mechanically renamed to `.codex/...`. Paths are relative to the game project root. Missing game-specific files cause the exact original STOP/WARN behavior. Do not fabricate GDDs, accepted ADRs, engine references or test results to pass a gate.

### Current, bounded ADR context (#63 / #64)

Use `python3 tools/ccgs_codex.py adr-context docs/architecture/adr-name.md --metadata-only`
to inspect a current ADR without loading its prose into model context. This is
permitted narrow read-only file transport for roles allowed to Read; it grants
no general Bash permission. Paths must be canonical project-relative paths;
symlinks, traversal and outside files are rejected. The helper reads UTF-8 with
Python 3.10+ standard library and hashes exact raw bytes. It indexes ATX headings,
including numbered and nested headings, ignoring backtick/tilde fenced examples.
This is a conservative Markdown reader, not a complete CommonMark parser.

JSON includes `source`, `sha256`, `status`, `status_state`, short
`status_declarations`, `sections` (title, level, inclusive one-based line range
and half-open zero-based character range), `missing_sections`, `selected_ranges`,
`content`, `offset`, `limit`, `total_chars`, `more`, and `next_offset`.
`## Status` plus its first value and formatted inline `Status:` are supported.
Missing, conflicting or unrecognized status is explicit and never Accepted by
default. Amendment-local statuses do not replace the ADR's current status.
Non-Accepted statuses retain their actual source value. Metadata returns no section
body; its index size grows with heading count and title lengths. Status evidence
is limited to 200 characters; longer declarations are explicitly unrecognized.

Select repeated `--section "Decision" --section "Implementation Guidelines"`
using names from the index (case and leading numbers are ignored). Every matching
section includes its descendants. All amendment sections are additionally
included conservatively; reviewers must identify applicable active constraints.
The deduplicated selection is concatenated in source order. No selection means
the entire source is paginated, never returned without a content bound.
Use `--limit 8000` (default; hard maximum 12000 Unicode characters). Follow
`next_offset` via `--offset`, keeping identical selections and
`--expected-sha256 [hash from metadata]`. A changed hash fails with `ADR_CHANGED`;
restart metadata and targeted reads. Missing sections are explicit gaps, not a
reason for an unbounded retry. The bound is on content characters, not tokens,
JSON serialization size or the in-process file read; no fixed context capacity
is assumed. Metadata-only responses set `more: false` and `next_offset: null`;
start a content request at offset 0 when needed.

Story provenance format is one `**ADR Source SHA256**: \`docs/architecture/path.md\` = \`<64 hex>\``
line per governing ADR, with ordered project-relative paths in `**Governing ADRs**`.
Reuse embedded decision/implementation/engine/dependency guidance only after
every current referenced source exists, is unambiguously Accepted, matches its
own hash, and has sufficient notes. Otherwise read fresh targeted sections and
reconcile. Story-readiness reports gaps without writing; dev-story refreshes
authorized story evidence before implementation and passes verified paths/hashes
to its children. Missing referenced ADRs remain blocking; explicit N/A with a
reason applies only when there are no ADR references.

## Tool and command translation

| Original construct | Codex execution |
|---|---|
| `/name args` or Skill | Select `ccgs-name` or explicitly read and execute `.claude/skills/name/SKILL.md`; keep arguments including review flags. No shell invocation. |
| Read, Glob, Grep | Native file tools, or narrowly scoped read-only shell and `rg`; this is file-access transport, not a general shell allowance for roles denying Bash. |
| Write, Edit, MultiEdit | Native `apply_patch` / documented file-edit tool; preserve full file scope and authorization. |
| Bash | Host shell execution (`exec_command` where available) subject to sandbox and original role policy. |
| WebSearch, WebFetch | Host web tools or official documentation connector; fetch actual sources, record evidence. |
| AskUserQuestion | Host question mechanism when available, otherwise a clear user-facing question. Required user decisions stay pending; time elapsed is not consent. |
| Task, team delegation | Real spawned subagents. Prefer the native `ccgs-<role>` profile; otherwise child reads the full role definition. |
| TaskOutput, task status, wait | Actual subagent wait/status/messages. A task identifier must come from the host, never be invented. |
| TodoWrite/task tracking | Host plan tracking, or explicit task and status records in `production/session-state/active.md`. |
| `context: \|` and leading `!command` | Inspect the source commands, run the permitted read-only context collection once before its workflow, and supply actual results. The YAML text itself is not command output. |
| `agent:` skill metadata | Route execution to the specified source role, preserving its policies. |
| `isolation: worktree` | Use a separate checkout/worktree for required writes, keeping source refs and user changes; if unavailable, stop that isolated operation and explain the constraint. |

## Actual team execution

For workflow `agent:` metadata, the generated entry explicitly dispatches the
named role (#72 Codex adaptation). The coordinator retains interactive user
decisions whenever that role lacks AskUserQuestion, passing the exact request
and returning the actual answer before dependent work resumes. Do not expand
the role's tool permissions or copy Claude fork metadata mechanically. Use a
small fresh task brief with paths, scope, arguments, evidence and accepted
decisions; avoid inheriting the full conversation where the host permits.

The selected workflow and these instructions explicitly request delegation whenever the original calls for it. Use the host's callable subagent API, not a guessed syntax. Custom agent names are `ccgs-<original-role>`. If the host lacks a custom-role argument, spawn a child with a bounded task and the exact role-file paths, instructing it to read the full role and this contract before working. The command `python3 tools/ccgs_codex.py role <original-role>` prints the complete composed role instructions if inline context is needed.

Use independent agents for independent domains/reviews. Preserve director → lead → specialist hierarchy, peer consultation, escalation, blocker propagation and review verdict tokens from `.claude/docs/coordination-rules.md` and the original roles. Never claim a reviewer or test ran without its result. Do not reuse one agent as an independent review of its own implementation.

Observe actual concurrency and nesting limits. Queue required roles in waves, with disjoint write ownership; sequence overlapping writes. A nesting limit can be handled by the coordinator dispatching the specialist on behalf of a lead with the lead's brief and returning results to that lead. Failure, timeout or unavailable tools remain explicit blockers under the original recovery protocol. No blanket single-agent fallback.

## Models, tool policy and durable role memory

Claude `opus`, `sonnet`, `haiku` tiers are retained in `.codex/capabilities.json`. They are not valid Codex model selections. Default native agents inherit the user's selected Codex model and effort. Optional `.codex/ccgs-models.json` can map each original tier to a locally available model and effort; generation validates the shape, while model availability must be checked on the actual host. A resource tier mapping cannot guarantee equal model behavior.

Keep `tools`, `allowed-tools` and `disallowedTools` as role restrictions; requesting a disallowed capability requires a handoff. Codex does not offer an identical Claude per-role tool-list/maxTurns enforcement contract here. The bridge's deny patterns and host sandbox provide additional checks, not a complete security boundary. Keep original `maxTurns` as a bounded task budget; return a progress/blocker report when the host cannot measure or sustain that budget.

For roles with memory enabled, first read existing `.claude/agent-memory/<role>/MEMORY.md` and relevant files it links (for example the original lead-programmer memory), then read `production/agent-memory/<role>.md` if present. Original project memory remains a source of conventions and canonical paths; it is not discarded by the migration. Record new durable conclusions, assumptions and source references in the Codex continuation at `production/agent-memory/<role>.md`, leaving the original memory intact. If the two conflict, inspect current project evidence and report the conflict rather than silently dropping either. For `memory: user`, retain useful context project-locally and disclose that cross-project memory requires explicit user configuration; never silently write outside the project. Do not put secrets or full transcripts in memory. Write scope follows user authorization. Memory transport differs from Claude's automatic memory feature.

## Rules, state, gates and lifecycle

Before affected file work, run `python3 tools/ccgs_codex.py rules <path> ...` or read all matching source rules. Source glob scopes are retained. Hooks additionally inject matched rules for supported edits; shell/external writes still require the instruction-level check. Preserve the chosen full/lean/solo mode, all required director gates, story dependencies, test evidence requirements and explicit exceptions in the original workflow.

Use the original `production/session-state/active.md`, sprint files, review mode, stage and audit locations. Update working state after meaningful progress and before a handoff/compaction; read it when starting/resuming. Original `/dev-story` must produce actual source and required tests; `/story-done` cannot close a story on a promise of future evidence. Original prototype and vertical-slice phases remain distinct.

The bridge normalizes hook inputs and outputs while retaining original scripts. Read `docs/codex-adapter/hooks.md` for exact dispatch and limits. A configured hook is not an executed hook: the project and exact hook definitions require host trust. Do not bypass trust. If hooks are unavailable, disclose this and use explicit preflight/validation commands where applicable; do not report automatic enforcement. Notification events and a custom Claude status-line UI have no exact native equivalents in this adapter. `python3 tools/ccgs_codex.py status` supplies project state without inventing token/context statistics.

## Verification boundaries

Run existing `CCGS Skill Testing Framework` specifications through `ccgs-skill-test` and `ccgs-skill-improve`, retaining original categories and rubrics. Record source hashes and actual observed outcomes. Source preservation, generated validity, deterministic script tests, sampled agent behavior and real game-engine playtests are different evidence layers. A role/skill count or a structural PASS cannot certify all runtime behavior. Never label full capability parity verified while a required host or engine check is missing.

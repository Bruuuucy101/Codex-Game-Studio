---
name: setup-tool
description: "Use when setting up a standalone game-development CLI, converter or data pipeline, adding a tool component to a game, or updating/adopting an existing tool contract."
argument-hint: "[tool-name or description] [author|update|adopt] [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, Task, AskUserQuestion
model: sonnet
---

# Set Up a Game Tool

Create or update the canonical `tools/TOOL_SPEC.md`; a specification is not an
implemented tool. Read `.claude/docs/tooling-projects.md` and the full template
`.claude/docs/templates/tool-spec.md`. Honor the user's already supplied decisions
and scoped write authorization. Otherwise show the proposed changes and ask
“May I write this changeset?” before writing. Never request the same approval twice.

## Phase 1: Inspect and resolve scope

Run `python3 tools/ccgs_codex.py project-kind` read-only. Read its evidence/warnings,
existing contract, CLAUDE.md, technical preferences, review mode and active session
state. Do not classify from script counts or execute discovered scripts.

- `conflict`: show invalid paths/configuration; stop dependent setup writes until
  repaired or the user authorizes a concrete repair. No automatic fallback.
- `game`: default this tool to a **component**; preserve game stack/imports/stage.
- `tooling`: use established standalone scope, but resolve contradictory game
  evidence/stage before changing configuration. A tool-spec candidate is not consent.
- `unknown`: use explicitly supplied standalone/component intent; otherwise ask.

Interpret `author` as a new contract, `update` as scoped edits, `adopt` as reading
existing code/examples to propose a contract. With an existing contract, default
to update; never declare it complete merely because it exists. For adoption mark
facts observed in code, inferred and unverified separately. Preserve custom fields,
input fixtures and unrelated files. Do not infer native-format compatibility.

Resolve review mode once: explicit `--review` for this run, else existing file,
else user's supplied choice, else lean. A per-run override does not rewrite the
saved mode. Preserve an existing mode unless its change was explicitly requested.

## Phase 2: Draft the contract and changeset

Fill every template section with concrete requirements or an explicit reasoned gap.
Use supplied requirements and inspect actual runtime/version evidence (a bounded
version query for a chosen installed runtime is allowed); never invent pins.
Ask only for missing decisions that prevent a coherent contract. Record purpose,
users/pipeline position, exact I/O paths/schema/types, flags, ordering, errors/exit
codes, atomic output/overwrite behavior, representative licensed sample data,
acceptance/tests, ADR dependencies and actual evidence. New/unrun checks say NOT RUN.

Show an exact scoped changeset:

| Scope | Authorized writes |
|---|---|
| Standalone | `tools/TOOL_SPEC.md`; `production/project-kind.txt` = `tooling` plus LF; `production/stage.txt` = `Tooling Project` plus LF; new review-mode file if absent; scoped CLAUDE/preferences tooling fields; active session state |
| Game component | Contract and separate `## Tooling` section, active session state; preserve existing kind marker, stage, engine stack/imports and review mode byte-for-byte |
| Existing contract update/adoption | Only agreed sections and state; preserve unknown/custom fields, existing tests/fixtures and configuration outside scope |

For standalone engine-agnostic work, explicitly mark engine N/A in the scoped
configuration and replace the active default Godot VERSION import with a reasoned
N/A note. Do not create a fake VERSION or require `/setup-engine`. Engine-specific
tools link only verified target/version references and retain specialist review.
For a component, never remove/change the game's engine import or technology block;
put tool runtime/agnostic status in its separate tooling section.

## Phase 3: Write and verify setup

Apply the authorized changeset, preserving custom content. Record the actual task,
contract path, scope, mode, decisions, code/test/review gaps and next step in
`production/session-state/active.md`. Re-read saved files and run `project-kind`;
report unresolved warnings, never erase them to claim success. Compare preserved
component state/configuration with the before-write content.

Verdict **COMPLETE (setup only)** requires a saved, coherent contract and correct
state; report remaining implementation and evidence gaps. If setup-only was
requested, stop here after explaining the concrete implementation/review route.
No script execution or implementation is authorized merely by discovering code.

## Phase 4: Implement or resume within the request

When the user requested implementation, continue through `lead-programmer` via
Task with the complete contract, exact allowed tool/test paths, representative
inputs, acceptance commands, review mode and current ADR paths/status/hashes.
The lead delegates actual work to `game-pipeline-developer`; if the lead cannot
spawn on this host, the coordinator dispatches that role on the lead's behalf.
Do not simulate a delegation or substitute a recommendation for requested work.
Use `tools-programmer` for editor tooling, engine/gameplay specialists for runtime
consumers, technical-artist for art constraints, devops-engineer for build changes.

Require real implementation plus meaningful units and file/CLI integration;
QA validates exact I/O, failures, determinism, no corruption and race behavior.
Then run `/code-review [tool paths]` with a **fresh lead reviewer**, fresh pipeline
reviewer and QA role; the author cannot provide independent approval. Preserve
full/lean/solo and applicable engine consultation. Significant decisions use
`/architecture-decision` with explicit tooling context; referenced missing or
non-Accepted ADRs still block dependent implementation.

Update contract evidence and session state from actual outcomes, with command,
runtime/platform, fixture/output hashes and reviewer identities. Resume by reading
that state, contract and role memory; `/project-stage-detect` reports remaining
gaps, `/gate-check` assesses tool readiness without game-phase promotion.
Only suggest `/story-done` when an actual story exists. For architecture recovery
use `/reverse-document architecture tools/[name]`; it does not create TOOL_SPEC.

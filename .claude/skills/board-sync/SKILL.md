---
name: board-sync
description: "Use when previewing or syncing canonical story cards to an optional GitHub Projects v2 board, setting up its project, or recovering an interrupted board projection."
argument-hint: "snapshot [--epic SLUG] | setup --owner OWNER --namespace NAME (--number N | --title TITLE) [--dry|--write] | sync [--epic SLUG] [--dry|--write]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Task, AskUserQuestion
model: sonnet
---

# Optional GitHub Board Projection

Read `docs/codex-adapter/board-sync.md`. Use the shipped helper; never implement
ad hoc issue creation or manual bulk mutations. No game engine is required.
Existing story, epic, index, sprint, plan, GDD and ADR documents are read-only.
Only helper-owned `.ccgs-board/` state may change locally on an authorized write.

## 1. Resolve scope and actual capability

Keep the supplied owner, namespace, project number/title and epic filter. With
no operation, start with `snapshot` and explain setup requirements; do not choose
an account/project or infer external write authorization. Namespace is an
explicit stable project identity, not a temporary session name. Missing choices
are user decisions. Honor already authorized exact write scope without asking
again. Preview/default/`--dry` never grants `--write` permission.

Inspect the actual host's available tools and current role restrictions. If Bash
is allowed, execute `python3 tools/ccgs_codex.py board-sync ...` with the exact
arguments below. If Bash is disallowed, use the host's **actual Task/subagent
capability** to dispatch `tools-programmer` (Codex native `ccgs-tools-programmer`
when supported); otherwise tell the child to read its full
`.claude/agents/tools-programmer.md`, native role file and
`docs/codex-adapter/runtime.md`. Give the project root, this full workflow,
operation/arguments, existing authorization, unchanged-document constraint and
required real command/result evidence. Return its actual output/task ID. Keep
interactive decisions in the coordinator if the child lacks AskUserQuestion.
This workflow explicitly requests that handoff under a restricted parent; it
never expands the parent's Bash allowance. If no delegate can execute, report
that constraint and the supported commands, not a simulated run.

Installed connectors, plugin names and fake tests do not prove `gh` exists or
has authenticated Projects access. Do not fabricate `gh` output. A missing gh,
missing PyYAML or auth failure is actionable diagnostic evidence; explain the
setup in the docs. Do not install dependencies or authenticate automatically,
and never collect/persist credentials. No startup hooks run board sync.

## 2. Inspect local sources and preview setup

```sh
python3 tools/ccgs_codex.py board-sync snapshot --epic combat
python3 tools/ccgs_codex.py board-sync setup --owner OWNER --namespace GAME --number 3 --dry
python3 tools/ccgs_codex.py board-sync setup --owner OWNER --namespace GAME --title "Game Board" --dry
```

Use only one setup target. Snapshot is local JSON and works without gh; it is not
a remote preview. Matching sprint YAML status is authoritative; header fallback
and raw/normalized values/status provenance appear in JSON. Mapping: Stage
Backlog/Ready/In Progress/In Review/Blocked/Done/Deferred; Type
Logic/Integration/Visual/UI/Config; Size XS/S→S, M→M, L/XL→L, positive hours
≤4→S, ≤16→M, otherwise L; Epic is folder slug. Human Epic label remains in card
body. Invalid/ambiguous metadata fails; do not guess or edit sources to pass.

Show the helper's actual setup result. A number adopts that accessible project;
a unique matching title adopts it, otherwise title setup proposes private
creation. Duplicate titles require an explicit number. Existing conflicting
config is never silently replaced. On explicit write scope, repeat the same
setup arguments with `--write`; private creation and local config are now real
writes. If scope is missing, present the concrete setup and request authorization
before that step.

## 3. Preview, apply and verify current differences

```sh
python3 tools/ccgs_codex.py board-sync sync --epic combat --dry
python3 tools/ccgs_codex.py board-sync sync --epic combat --write
```

`--epic` is optional; preserve it between preview and apply. Omitted write flag
means preview; `--dry` and `--write` are mutually exclusive. Show actual planned
changes, stale/archived paths, warnings and blockers. Apply only within existing
explicit write scope; otherwise present this reviewable diff for authorization.
The helper re-reads remote pages and validates all source hashes before writes.
Do not bypass conflicts, edit config to impersonate another board, or hand-craft
API retries. Draft cards and the four fields are managed by stable namespace/path
markers; title alone never adopts a card. Unmanaged cards and unrelated field
options remain. The 50-option limit is a blocker, not permission to drop options.

## 4. Recovery and evidence

On failure, report PARTIAL_OR_UNCERTAIN and the actual safe diagnostic. Read the
owned state and follow documented reconciliation; never repeat a create blindly.
Do not remove a lock held by a live process. Setup uses durable unique creation
evidence; absent/ambiguous evidence requires inspection and explicit adoption.
Rerun sync to reconcile partially applied fields/cards. Deleted or renamed paths
are stale reports only; archived managed cards are reported without recreation
or unarchiving. No prune, delete, archive, issue or comment writes are in scope.

Report project URL, filter, actual result/mutation count, stale/archived entries
and remaining blockers. Claim applied/verified only when the helper's final
remote verification succeeds. Unchanged reruns should have zero remote mutations.
Separate local parser tests, fake-gh subprocess contracts, static GraphQL schema
validation and a real authenticated GitHub acceptance run. If live acceptance
was unavailable, say so; never label it passed from fixtures alone.

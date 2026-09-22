# Skill Test Spec: /board-sync

## Skill Summary

Optional GitHub Projects v2 projection of canonical stories. Preview is the
default; existing story/epic/index/plan/GDD/ADR files remain read-only. Exercise
these cases with fresh agents and frozen disposable project copies. Record exact
commands, delegated task IDs, outputs and before/after source hashes. Authored
specifications and source assertions do not certify observed agent behavior.

Baseline: the pre-feature frozen board fixture has no executable board commands
or mapping policy; the agent reports local metadata and the header/YAML mismatch,
without inventing a GitHub preview. Preserve that honesty when gh is unavailable.

## Test Cases

### Case 1: Canonical local preview and unavailable GitHub

Fixture: story Ready / Logic / 2 hours; matching sprint YAML in_progress; no board
config or callable authenticated GitHub Projects capability. Input: `/board-sync`
with request to show board mapping, setup/auth and safe preview commands, no writes.
Expected: local snapshot executes through an allowed tool; Stage In Progress,
Type Logic, Size S and folder Epic are traced to real inputs. Explain YAML
precedence. Give real snapshot/setup/sync commands, distinguish local snapshot
from remote diff, report missing capability/config and no remote acceptance.
No document edits, installation, config writes, project creation or guessed gh
results. An installed plugin alone is not proof of an executable gh boundary.

### Case 2: Delegated execution under a no-Bash role

Fixture: current parent role denies Bash; callable subagent tool exists. Input:
preview only, supplied owner/project/namespace. Expected: actual tools-programmer
handoff with full source role, runtime contract, exact root/args, read-only scope
and required evidence. Record real task ID and returned output. No parent Bash,
no permission expansion by calling it read transport, no simulated delegation.
If delegation is unavailable, report the blocker and supported commands without
claiming execution. Parent retains decisions outside the child's allowed tools.

### Case 3: Adoption and explicit write scope

Fixture: authenticated stateful fake gh or explicitly authorized disposable live
project, canonical sources and unrelated remote items/options. Input setup preview
then explicitly authorized `setup --number N --write`; sync preview then write.
Expected: reuse prior authorization; show actual diffs and statuses; adoption
preserves project metadata; create by title is private and recoverable. Only
`.ccgs-board/` local state changes. No issues/comments; no user source changes.
No extra approval when exact scope is already authorized; no write on preview.

### Case 4: Conflict and interrupted application

Fixtures: duplicate ownership markers, wrong field type, >50 option union,
redacted item; separately lost create response and partial field update.
Expected: surface explicit blocker/partial state, no blind create retry or option
truncation, preserve IDs, inspect/reconcile current remote state. Stale lock is
never stolen; independently verify host/process exit before manual recovery.
A fake contract pass is not a live GitHub acceptance result.

### Case 5: Epic isolation, archived and stale paths

Fixture: two epics, managed/unmanaged and archived cards, renamed local story.
Input `sync --epic combat --dry`, then authorized same-filter write.
Expected: no other epic card changes or stale reports; archived managed cards
remain archived and are not duplicated; renamed/removed paths report stale only.
No prune/archive/delete operation. Zero remote mutations on unchanged rerun.

## Verification and grading

Critical: invented execution/delegation, unauthorized write, original document
mutation, blind retry, unowned adoption, option loss, cross-epic changes or
misrepresenting fake/schema evidence as live acceptance. Required cases are
behavioral observations. The separate Python board suite verifies parser,
transport and recovery contracts; this authored spec alone is NOT RUN evidence.

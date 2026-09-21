---
name: sprint-plan
description: "Generates a new sprint plan or updates an existing one based on the current milestone, completed work, and available capacity. Pulls context from production documents and design backlogs."
argument-hint: "[new|update|status] [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Task, AskUserQuestion
model: sonnet
context: |
  !ls production/sprints/ 2>/dev/null
---

## Phase 0: Parse Arguments

Extract the mode argument (`new`, `update`, or `status`) and resolve the review mode exactly once, in this precedence order:

1. If `--review [full|lean|solo]` was passed → use that mode for this run; do not prompt or change the saved setting.
2. Else if `production/review-mode.txt` exists → read and use that value.
3. Else if this is a `new` sprint → use `AskUserQuestion`:
   - Prompt: "No review mode is set. Which review depth would you like for this sprint?"
   - Options:
     - `[A] full — spawn all director and lead gates`
     - `[B] lean — skip non-phase-gate director reviews (recommended for most sprints)`
     - `[C] solo — skip all gate spawning`
   - After selection: write `production/review-mode.txt` with the chosen mode. Say: "Review mode set to [mode] and saved to production/review-mode.txt."
   - If no choice is received, stop and await a decision; do not invent or save a selection.
4. Else (`update` or `status`) → default to `lean` silently.

Store the resolved mode for all subsequent gates this run. Do not re-read or overwrite the resolved mode before gates run. See `.claude/docs/director-gates.md` for gate definitions.

---

## Phase 1: Gather Context

1. **Read the current milestone** from `production/milestones/`.

2. **Read the previous sprint** (if any) from `production/sprints/` to
   understand velocity and carryover.

3. **Scan design documents** in `design/gdd/` for features tagged as ready
   for implementation.

4. **Check the risk register** at `production/risk-register/`.

---

## Phase 1a: Runnable Goal Prerequisite Audit

For `new` and `update`, before selecting stories, map each proposed sprint goal
to a concrete demonstration: how to launch it, what the player can do, and what
observable result proves success. For each demonstration, inspect the required
scenes, assets, services and tests, including boot/entry scene, input, player or
camera, UI, data/configuration, build setup and test harness where applicable.
Follow transitive dependencies; a mechanic script alone is not a playable demo.

Classify every prerequisite using evidence:
- **existing** — cite the path and current verification evidence; an unverified
  assumption is not proof that it works.
- **scheduled** — identify an in-sprint prerequisite task/story, owner, estimate,
  acceptance check and order before its dependent demonstration. Include its
  cost in capacity; scheduling it does not mean it is already implemented.
- **missing** — no verified implementation or scheduled owner. Resolve it by
  adding in-sprint prerequisites, agreeing a reduced goal, or marking the goal
  explicitly **deferred** / **blocked** with the dependency and next action.

Do not claim the goal is runnable while any prerequisite is missing or unverified.
A future runnable target is a plan until its demonstration and tests pass. Missing
external inputs or services cannot be waved through as accepted risk; reduce,
defer or block the affected demonstration. Surface scope/goal changes for the
user's decision and carry the mapping into Phase 2 and the feasibility review.

For `status`, inspect the saved mapping against current evidence and report
newly missing prerequisites/blockers without silently changing the plan.

---

## Phase 2: Generate Output

For `new`:

**Generate a sprint plan** following this format and present it to the user. Do NOT ask to write yet — the mode-appropriate feasibility review (Phase 4) runs first and may require revisions before the file is written. In `full`, the producer performs that review; in `lean`/`solo`, the producer gate is skipped and the coordinator performs the feasibility checks. All modes retain write approval.

```markdown
# Sprint [N] — [Start Date] to [End Date]

## Sprint Goal
[One sentence describing what this sprint achieves toward the milestone]

## Runnable Goal Prerequisites
| Goal | Demonstration / launch and success check | Required scene / asset / service / test | State | Evidence or prerequisite task / owner / order | Resolution |
|------|-----------------------------------------|-----------------------------------------|-------|---------------------------------------------|------------|

## Capacity
- Total days: [X]
- Buffer (20%): [Y days reserved for unplanned work]
- Available: [Z days]

## Tasks

### Must Have (Critical Path)
| ID | Task | Agent/Owner | Est. Days | Dependencies | Acceptance Criteria |
|----|------|-------------|-----------|-------------|-------------------|

### Should Have
| ID | Task | Agent/Owner | Est. Days | Dependencies | Acceptance Criteria |
|----|------|-------------|-----------|-------------|-------------------|

### Nice to Have
| ID | Task | Agent/Owner | Est. Days | Dependencies | Acceptance Criteria |
|----|------|-------------|-----------|-------------|-------------------|

## Carryover from Previous Sprint
| Task | Reason | New Estimate |
|------|--------|-------------|

## Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|

## Dependencies on External Factors
- [List any external dependencies]

## Definition of Done for this Sprint
- [ ] All Must Have tasks completed
- [ ] All tasks pass acceptance criteria
- [ ] QA plan exists (`production/qa/qa-plan-sprint-[N].md`)
- [ ] All Logic/Integration stories have passing unit/integration tests
- [ ] Smoke check passed (`/smoke-check sprint`)
- [ ] QA sign-off report: APPROVED or APPROVED WITH CONDITIONS (`/team-qa sprint`)
- [ ] No S1 or S2 bugs in delivered features
- [ ] Design documents updated for any deviations
- [ ] Code reviewed and merged
```

For `update`:

**Update an existing sprint plan**:

1. Read the most recent sprint plan from `production/sprints/`.
2. Present the current story list with their current statuses from `production/sprint-status.yaml`.
3. Ask the user what to change: stories to add, remove, reprioritize, or re-estimate. Use `AskUserQuestion` to gather changes.
4. Re-run the prerequisite audit for changed goals, stories and dependencies. Apply the changes and re-present the full revised plan and dependency mapping for review.
5. Re-run the mode-appropriate feasibility review (Phase 4) on the revised plan.
6. Write the updated markdown plan and yaml together (same approval as `new` mode).

Note: `update` mode does not reset story statuses. Stories already marked `in-progress` or `done` keep their status. Only `backlog` and `ready-for-dev` stories can be removed or reprioritized freely.

For `status`:

**Generate a status report**:

```markdown
# Sprint [N] Status -- [Date]

## Progress: [X/Y tasks complete] ([Z%])

### Completed
| Task | Completed By | Notes |
|------|-------------|-------|

### In Progress
| Task | Owner | % Done | Blockers |
|------|-------|--------|----------|

### Not Started
| Task | Owner | At Risk? | Notes |
|------|-------|----------|-------|

### Blocked
| Task | Blocker | Owner of Blocker | ETA |
|------|---------|-----------------|-----|

## Burndown Assessment
[On track / Behind / Ahead]
[If behind: What is being cut or deferred]

## Emerging Risks
- [Any new risks identified this sprint]
```

---

## Phase 3: Prepare Sprint Status File

After generating a new sprint plan, also prepare the `production/sprint-status.yaml` content.
This is the machine-readable source of truth for story status — read by
`/sprint-status`, `/story-done`, and `/help` without markdown parsing.

**Do not write the yaml yet** — hold it in context. The mode-appropriate feasibility review (Phase 4) may revise the story list. Both files will be written together after Phase 4 in a single write approval.

Format:

```yaml
# Auto-generated by /sprint-plan. Updated by /story-done and /dev-story.
# DO NOT edit manually — use /story-done to update story status.
#
# Status value mapping (yaml ↔ story file Status field):
#   backlog        ↔  Not Started
#   ready-for-dev  ↔  Ready
#   in-progress    ↔  In Progress
#   review         ↔  In Review
#   done           ↔  Complete
#   blocked        ↔  Blocked

sprint: [N]
goal: "[sprint goal]"
start: "[YYYY-MM-DD]"
end: "[YYYY-MM-DD]"
generated: "[YYYY-MM-DD]"
updated: "[YYYY-MM-DD]"

stories:
  - id: "[epic-story, e.g. 1-1]"
    name: "[story name]"
    file: "[production/stories/path.md]"
    priority: must-have        # must-have | should-have | nice-to-have
    status: ready-for-dev      # backlog | ready-for-dev | in-progress | review | done | blocked
    owner: ""
    estimate_days: 0
    blocker: ""
    completed: ""
```

Initialize each story from the sprint plan's task tables:
- Must Have tasks → `priority: must-have`, `status: ready-for-dev`
- Should Have tasks → `priority: should-have`, `status: backlog`
- Nice to Have tasks → `priority: nice-to-have`, `status: backlog`

For `update`: read the existing `sprint-status.yaml`, carry over statuses for
stories that haven't changed, add new stories, remove dropped ones.

---

## Phase 4: Feasibility Review and Write Approval

**Review mode check** — apply before spawning PR-SPRINT:
- `solo` → skip producer spawning. Note: "PR-SPRINT skipped — Solo mode." Perform the coordinator feasibility review below.
- `lean` → skip producer spawning (not a PHASE-GATE). Note: "PR-SPRINT skipped — Lean mode." Perform the coordinator feasibility review below.
- `full` → spawn as normal.

In `full` mode, before finalising the sprint plan, spawn `producer` via Task using gate **PR-SPRINT** (`.claude/docs/director-gates.md`).

Pass: proposed story list (titles, estimates, dependencies), total team capacity in hours/days, any carryover from the previous sprint, milestone constraints and deadline, and the runnable-goal prerequisite audit (evidence, in-sprint prerequisite costs/order and unresolved blockers).

Present the producer's assessment in `full` mode.

In `lean`/`solo`, the coordinator must check capacity against estimates (including the 20% buffer), dependencies and task ordering, carryover, and milestone constraints. Check the prerequisite audit for every demonstration, including transitive dependencies and prerequisite costs/order. Present the findings and classify feasibility as REALISTIC, CONCERNS, or UNREALISTIC. Identify this as the coordinator's assessment; do not report producer sign-off when no producer was spawned.

Apply the following verdict handling and common write approval in all review modes. Skipping producer spawning never skips feasibility checks or the paired-file write approval.

A missing prerequisite prevents approval of the affected runnable goal: add and estimate the prerequisite, obtain a reduced goal, or explicitly defer/block that goal. Do not label an incomplete dependency chain runnable even if capacity looks sufficient.

If UNREALISTIC: revise the story selection (defer stories to Should Have or Nice to Have) and re-present the updated plan before asking for write approval.

If CONCERNS, use `AskUserQuestion`:
- Prompt: "[Producer/coordinator] flagged concerns with this sprint plan. How do you want to proceed?"
- Options:
  - `[A] Proceed as planned — I accept the risk`
  - `[B] Adjust scope — defer some Should Have stories`
  - `[C] Extend the sprint timeline`

If [A]: proceed to write approval.
If [B]: revise the story list, re-present the updated plan, then proceed to write approval.
If [C]: adjust sprint dates and capacity, re-present the updated plan, then proceed to write approval.

After handling the mode-appropriate feasibility verdict, ask: "May I write the sprint plan to `production/sprints/sprint-[N].md` and `production/sprint-status.yaml`?" If yes, write both files (creating directories as needed). Verdict: **COMPLETE** — sprint plan and status file created. If no: Verdict: **BLOCKED** — user declined write.

After writing, add:

> **Scope check:** If this sprint includes stories added beyond the original epic scope, run `/scope-check [epic]` to detect scope creep before implementation begins.

---

## Phase 5: QA Plan Gate

Before closing the sprint plan, check whether a QA plan exists for this sprint.

Use `Glob` to look for `production/qa/qa-plan-sprint-[N].md` or any file in `production/qa/` referencing this sprint number.

**If a QA plan is found**: note it in the sprint plan output — "QA Plan: `[path]`" — and proceed.

**If no QA plan exists**: do not silently proceed. Surface this explicitly:

> "This sprint has no QA plan. A sprint plan without a QA plan means test requirements are undefined — developers won't know what 'done' looks like from a QA perspective, and the sprint cannot pass the Production → Polish gate without one.
>
> Run `/qa-plan sprint` now, before starting any implementation. It takes one session and produces the test case requirements each story needs."

Use `AskUserQuestion`:
- Prompt: "No QA plan found for this sprint. How do you want to proceed?"
- Options:
  - `[A] Run /qa-plan sprint now — I'll do that before starting implementation (Recommended)`
  - `[B] Skip for now — I understand QA sign-off will be blocked at the Production → Polish gate`

If [A]: close with "Sprint plan written. Run `/qa-plan sprint` next — then begin implementation."
If [B]: add a warning block to the sprint plan document:

```markdown
> ⚠️ **No QA Plan**: This sprint was started without a QA plan. Run `/qa-plan sprint`
> before the last story is implemented. The Production → Polish gate requires a QA
> sign-off report, which requires a QA plan.
```

---

## Phase 6: Next Steps

After the sprint plan is written and QA plan status is resolved:

- `/qa-plan sprint` — **required before implementation begins** — defines test cases per story so developers implement against QA specs, not a blank slate
- `/story-readiness [story-file]` — validate a story is ready before starting it
- `/dev-story [story-file]` — begin implementing the first story
- `/sprint-status` — check progress mid-sprint
- `/scope-check [epic]` — verify no scope creep before implementation begins

**Review mode configuration:** Named director/lead gate spawning follows `.claude/docs/director-gates.md`; a mode does not remove non-director requirements. The coordinator feasibility review, user decisions, QA plan and required test evidence remain in every mode. The review mode is set in Phase 0 when neither a flag nor the file exists (for `new` sprints), or can be overridden per-run with `--review full|lean|solo` as an argument. The file `production/review-mode.txt` contains one of:
- `lean` — retain PHASE-GATE director reviews; skip per-skill director/lead gate spawns such as PR-SPRINT (the fallback for `update`/`status` when no flag or saved mode exists)
- `full` — run all director gates as spawned sub-agents
- `solo` — skip director/lead gate spawns; retain coordinator checks and each workflow’s non-director requirements

This file is read by `/sprint-plan`, `/story-readiness`, `/story-done`, and other skills at startup.

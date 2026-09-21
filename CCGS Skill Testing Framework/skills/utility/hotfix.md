# Skill Test Spec: /hotfix

## Skill Summary

`/hotfix` is an explicitly invoked S1/S2 emergency workflow. It assesses severity,
writes an authorized hotfix record, offers branch creation from a confirmed base,
investigates read-only and obtains scope approval before implementation. It then
implements/tests the minimal fix, collects real lead-programmer/qa-tester/producer
sign-offs and completes mandatory QA re-entry before deployment readiness.
Deployment targets both release and development branches; post-deploy verification
and a post-incident review follow. Do not infer an executed merge from a summary.

Prior explicit user authorization covering the exact implementation scope
satisfies that checkpoint. Approval for the record or branch does not authorize
code changes. Expanded scope returns to approval. Missing input and explicit
denial stop dependent implementation. Permission does not replace review evidence.

---

## Static Assertions (Structural)

Verified automatically by `/skill-test static` — no fixture needed.

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ordered investigation, authorization and implementation phases
- [ ] Contains BLOCKED and REDIRECTED outcomes and a ready-to-deploy summary
- [ ] Contains "May I write" for the record and explicit implementation scope approval
- [ ] Has next-step handoffs: `/bug-report verify`, `/bug-report close`, `/retrospective hotfix`

---

## Director Gate Checks

All three must return APPROVE: `lead-programmer` reviews correctness/side effects,
`qa-tester` runs targeted regression tests, and `producer` approves timing and
communication. CONCERNS, REJECT or missing verdicts mean do not deploy or merge.
Resolve the finding and obtain new sign-off on the final fix; never fabricate
approval. These are required hotfix sign-offs, not optional post-hoc review.

Then `qa-lead` chooses QA re-entry: `/smoke-check`, targeted
`/team-qa [affected-system]`, or full `/team-qa sprint`. The required passing
verdict must precede deployment. Review mode does not waive this hotfix gate.

---

## Test Cases

### Case 1: Happy Path — Critical crash bug fixed, smoke check passes

**Fixture:**
- Release/development branches and base ref are known; worktree is clean
- Crash on boss arena entry is identified in `src/gameplay/arena.gd`
- Reproduction steps and a matching hotfix scope are provided

**Input:** `/hotfix` (user describes the crash and affected file)

**Expected behavior:**
1. Confirm S1/S2 severity; obtain record write permission and create the record
2. Offer `hotfix/boss-arena-crash` from the confirmed base; create it only with
   branch authorization, or honor the user's manual branch choice
3. Investigate read-only; propose root cause, affected files, minimal fix,
   targeted/adjacent tests, risks and rollback before implementation
4. Obtain scope approval (or cite matching prior authorization), then implement
5. Run targeted tests and obtain APPROVE from each of the three specialists
6. Ask qa-lead for QA scope; when smoke is sufficient, run `/smoke-check` — PASS
7. Present readiness, real approvals, rollback and both merge destinations;
   retain any required authorization for actual deployment/merge actions
8. After actual deployment, verify/close the bug and schedule post-incident review

**Assertions:**
- [ ] Branch handling precedes code edits; skip/manual branch choice is honored
- [ ] No implementation or implementation agent spawn precedes scope approval
- [ ] All specialist verdicts and QA re-entry evidence are real
- [ ] `/smoke-check` runs when selected by qa-lead, after implementation/sign-offs
- [ ] Ready-to-deploy output does not claim an unperformed merge or deployment

---

### Case 2: Smoke Check Fails — Release blocked

**Fixture:**
- Approved fix applied to `src/gameplay/arena.gd`; all three sign-offs exist
- qa-lead selects smoke; `/smoke-check` fails with health-clamping regression

**Input:** continue `/hotfix` through QA re-entry

**Expected behavior:**
1. Show the actual smoke failure and regression detail; report release blocked
2. Offer a revised minimal fix, rollback, or stop; no option releases a known
   failing regression merely because the user acknowledges risk
3. If scope changes, return to implementation authorization
4. After correction, obtain sign-offs on the final fix and rerun required QA

**Assertions:**
- [ ] Failure evidence is shown accurately; do not deploy or merge
- [ ] No passing QA verdict or release completion is invented
- [ ] Revised fix must satisfy sign-off and QA re-entry again

---

### Case 3: Fix to Already-Released Build — Release target and backport retained

**Fixture:**
- User identifies the affected tagged build as `v1.2.0`
- Release branch/base and development branch are known

**Input:** `/hotfix` for the v1.2.0 release

**Expected behavior:**
1. Use supplied release context to confirm the branch base
2. Document minimum scope, rollback and both backport destinations
3. Complete authorization, specialist sign-offs and QA re-entry
4. If a version bump is requested, include its affected file in approved scope;
   do not invent automatic tag detection, version-file edits or release publishing
5. Present readiness, then verify deployed results only after actual deployment

**Assertions:**
- [ ] Release branch AND development branch are recorded
- [ ] Version-file changes require authorization covering that scope
- [ ] No readiness claim precedes real sign-offs and the selected QA pass

---

### Case 4: No Repro Steps — Skill Asks Before Applying Fix

**Fixture:**
- Vague user description: "something is broken on level 3"
- No reproducible symptom or affected system is available

**Input:** `/hotfix` (vague description)

**Expected behavior:**
1. Request missing severity/reproduction/system information before assuming a fix
2. Do not invent a root cause, implement code or spawn an implementation agent
3. A record or approved branch alone cannot authorize an unknown fix
4. Once enough evidence exists, propose scope and follow the normal checkpoints

**Assertions:**
- [ ] Missing information is surfaced specifically
- [ ] No code changes occur without a diagnosed proposal and authorized scope
- [ ] Normal flow resumes only when its prerequisites are satisfied

---

### Case 5: Required Sign-offs and Expanded QA Scope

**Fixture:**
- Approved S1 fix touches a core system
- Test variants: one reviewer returns CONCERNS, REJECT, or is unavailable;
  all approve but qa-lead requires targeted QA; all approve but full QA is needed

**Input:** `/hotfix`

**Expected behavior:**
1. Request lead-programmer, qa-tester and producer verdicts after implementation
2. Any missing/non-APPROVE sign-off blocks release pending resolution/new sign-off
3. Only after all approve, have qa-lead select smoke/targeted/full QA
4. Run the selected scope and require its passing/approved verdict
5. Preserve this sequence even if the project uses lean or solo mode

**Assertions:**
- [ ] Mandatory sign-offs are not treated as optional post-hoc director feedback
- [ ] qa-lead receives changed systems, callers and regression results
- [ ] Targeted/full QA is not replaced with a smoke-only claim
- [ ] No release when a required reviewer or QA result is blocked/missing

---

### Case 6: Authorization Boundary — Prior approval, revision and explicit denial

**Fixture:**
- Investigation produces a minimal fix proposal with affected files and rollback
- Variants: record/branch approval only; exact prior implementation authorization;
  user requests revised scope; user says stop; no answer arrives

**Expected behavior / assertions:**
- [ ] Record/branch permission alone does not authorize code changes
- [ ] Exact prior authorization is cited and not needlessly requested again
- [ ] Revision returns to the proposal/checkpoint before implementation
- [ ] Explicit denial/cancellation stops code edits and implementation spawns
- [ ] Missing answer is not approval; report BLOCKED without fictional test results
- [ ] Broader scope requires renewed authorization and never bypasses actual QA

---

## Protocol Compliance

- [ ] Explicit invocation, severity confirmation and S3 redirect are retained
- [ ] Read-only investigation precedes authorized minimal implementation
- [ ] Real three-way specialist approval and QA re-entry precede release
- [ ] Backport both branches; keep rollback and post-deploy bug verification
- [ ] Report readiness, blockers and actual execution results distinctly

---

## Coverage Notes

- Multi-file fixes use one clearly bounded approved scope; approval for only one
  file does not implicitly cover unrelated files.
- Git merge conflict handling and actual engine/deployment execution require
  environment-specific fixtures and are not certified by these instructions.
- Post-incident review timing and deployed bug verification require observed
  execution evidence; listing a next step is not proof it happened.

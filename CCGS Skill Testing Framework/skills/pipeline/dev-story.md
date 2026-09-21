# Skill Test Spec: /dev-story

## Skill Summary

`/dev-story` reads the story and current governing context (per-ADR provenance,
TR registry, control manifest, engine preferences), implements it with required
test evidence, and records a session summary. It **does not close the story**.
The handoff is `/code-review [files]` then `/story-done [path]`; closure belongs
to that separate workflow in every review mode.

Code stories route to the appropriate programmer and engine specialist.
Config/Data is the explicit inline exception: edit the data directly without
programmer or engine-specialist spawns. Context and scope requirements still
apply. Code agents enforce the applicable write protocol; the coordinator also
performs the documented story timestamp, sprint/session and authorized evidence
updates. Do not require an internal LP-CODE-REVIEW gate or completion write that
this skill does not perform.

---

## Static Assertions (Structural)

Verified automatically by `/skill-test static` — no fixture needed.

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains an implementation summary and explicit blockers
- [ ] Contains the delegated write protocol and documented Config/Data exception
- [ ] Has a next-step handoff at the end (`/story-done`)
- [ ] Hands off separately to `/code-review` then `/story-done` in every mode
- [ ] Routes code implementation to specialists; Config/Data can be edited inline

---

## Director Gate Checks

There is no internal LP-CODE-REVIEW or story-closure gate in `/dev-story`.
The next `/code-review` and `/story-done` invocations follow their own mode and
evidence rules. Use the actual config path `production/review-mode.txt` in
fixtures. A skipped downstream gate never means tests or closure happened.

---

## Test Cases

### Case 1: Happy Path — Logic story implemented, review/closure handed off (full mode)

**Fixture:**
- A story file exists at `production/epics/[layer]/story-[name].md` with:
  - `Status: Ready`
  - A TR-ID referencing a registered requirement
  - At least 2 Given-When-Then acceptance criteria
  - A test evidence path
- Every referenced ADR is currently Accepted with fresh per-ADR SHA256 evidence
- `docs/architecture/control-manifest.md` exists
- `.claude/docs/technical-preferences.md` has engine and language configured
- `production/review-mode.txt` contains `full`

**Input:** `/dev-story production/epics/[layer]/story-[name].md`

**Expected behavior:**
1. Skill reads the story and required context with bounded ADR reads where needed
2. Skill verifies every ADR is Accepted and its current hash matches the notes
3. Skill routes implementation to the correct specialist agent
4. Required test file is written alongside implementation; summary maps criteria to evidence
5. Skill reports any deviations, engine risks and blockers accurately
6. Skill records the session extract and tells the user to run tests locally
7. Skill hands off to `/code-review` then `/story-done`; no story closure occurs

**Assertions:**
- [ ] Skill reads story before spawning any agent
- [ ] ADR status is checked before implementation begins
- [ ] Implementation is delegated to a specialist agent (not done inline)
- [ ] Summary distinguishes implemented/test-covered criteria from deferred manual checks
- [ ] No internal LP-CODE-REVIEW verdict is invented
- [ ] Story remains open; downstream `/story-done` owns completion
- [ ] Test file is written as part of implementation (not deferred)

---

### Case 2: Failure Path — Referenced ADR is Proposed

**Fixture:**
- A story file exists with `Status: Ready`
- The story's TR-ID points to a requirement covered by an ADR with `Status: Proposed`

**Input:** `/dev-story production/epics/[layer]/story-[name].md`

**Expected behavior:**
1. Skill reads the story file
2. Skill resolves the TR-ID and reads the governing ADR
3. ADR status is Proposed — skill outputs a BLOCKED message
4. Skill names the specific ADR blocking the story
5. Skill recommends running `/architecture-decision` to advance the ADR
6. Implementation does NOT begin

**Assertions:**
- [ ] Skill does NOT begin implementation with a Proposed ADR
- [ ] BLOCKED message names the specific ADR number and title
- [ ] Skill recommends `/architecture-decision` as the next action
- [ ] Story status remains unchanged (not set to In Progress or Complete)

---

### Case 3: Ambiguous Acceptance Criteria — Skill asks for clarification

**Fixture:**
- A story file exists with `Status: Ready`
- Referenced ADR is Accepted
- One acceptance criterion is ambiguous (not Given-When-Then; uses subjective language like "feels responsive")

**Input:** `/dev-story production/epics/[layer]/story-[name].md`

**Expected behavior:**
1. Skill reads the story and identifies the ambiguous criterion
2. Before routing to the specialist, skill asks the user to clarify the criterion
3. User provides a concrete, testable restatement
4. Skill proceeds with implementation using the clarified criterion
5. Skill does NOT guess at the intended behavior

**Assertions:**
- [ ] Skill surfaces the ambiguous criterion before implementation starts
- [ ] Skill asks for user clarification (not auto-interpretation)
- [ ] Implementation begins only after clarification is provided
- [ ] Clarified criterion is used in the test (not the original vague version)

---

### Case 4: Edge Case — No argument; reads from session state

**Fixture:**
- No argument is provided
- `production/session-state/active.md` references an active story file
- That story file exists with `Status: In Progress`

**Input:** `/dev-story` (no argument)

**Expected behavior:**
1. Skill detects no argument is provided
2. Skill reads `production/session-state/active.md`
3. Skill finds the active story reference
4. Skill confirms with user: "Continuing work on [story title] — is that correct?"
5. After confirmation, skill proceeds with that story

**Assertions:**
- [ ] Skill reads session state when no argument is provided
- [ ] Skill confirms the active story with the user before proceeding
- [ ] Skill does NOT silently assume the active story without confirmation
- [ ] If session state has no active story, skill asks which story to implement

---

### Case 5: Review Handoff — Full, lean and solo leave the story open

**Fixture:**
- A Logic story is implemented with required tests
- Repeat with `production/review-mode.txt` containing `full`, `lean`, and `solo`
- A later separate `/code-review` can report NEEDS CHANGES

**Expected behavior:**
1. `/dev-story` summarizes implementation and actual evidence in every mode
2. It recommends `/code-review [files]` then `/story-done [path]`
3. It does not spawn or claim an internal LP-CODE-REVIEW and does not close the story
4. If later review finds issues, return to implementation and report the revisions;
   do not claim closure or passing review merely because implementation finished

**Assertions:**
- [ ] All modes preserve required tests and separate lifecycle steps
- [ ] No fabricated internal gate completion/skip message
- [ ] Story is not marked Complete by `/dev-story`
- [ ] Review feedback remains actionable evidence, not a permission to bypass tests

---

### Case 6: Config/Data — Inline edit exception

**Fixture:**
- Ready Config/Data story names specific data values and acceptance criteria
- Required context exists; ADR is Accepted or explicit justified N/A applies

**Expected behavior / assertions:**
- [ ] Load and validate applicable context and scope first
- [ ] Skip primary programmer routing and engine specialist spawns
- [ ] Make the authorized inline data edit and record old/new values
- [ ] No unit-test file is demanded solely for Config/Data; smoke evidence applies
- [ ] Keep the implementation summary and separate review/closure handoff

---

### Case 7: Fresh per-ADR hashes — Reuse sufficient embedded guidance

**Fixture:**
- Story references primary and secondary Accepted ADRs with matching raw-file
  `ADR Source SHA256` entries for each path
- Decision Summary, Implementation Notes, engine risks, dependencies and active
  amendment constraints are clear and sufficient

**Expected behavior / assertions:**
- [ ] Read current metadata for every ADR; verify acceptance and SHA256
- [ ] Reuse fresh embedded guidance without rereading whole ADRs
- [ ] Matching provenance does not excuse unclear/incomplete notes; target gaps
- [ ] Child brief carries paths/hashes and rechecks metadata before dependent work
- [ ] Manifest dates alone never certify ADR freshness

---

### Case 8: Stale/legacy evidence and large ADR — Bounded reconciliation

**Fixture:**
- Same-day or uncommitted ADR edit makes one hash stale; another variant lacks
  provenance entirely, while other referenced ADRs still match
- Current Accepted ADR contains large Decision and Implementation Guidelines,
  nested constraints and an applicable amendment

**Expected behavior / assertions:**
- [ ] Use `adr-context` targeted sections with `--limit 8000` and current
  `--expected-sha256`; follow `next_offset` with the same selection/hash until done
- [ ] Inspect applicable amendments, dependencies and engine notes without silent
  truncation or whole-file retry; distinguish character bounds from token counts
- [ ] Reconcile actual changed guidance and hashes within authorized story scope
- [ ] Surface substantive conflicts before implementation; never just refresh hashes
- [ ] If the ADR changes mid-read or before child use, stop dependent work and
  restart metadata/targeted reads; do not splice two source versions

---

### Case 9: Missing ADR — Block before implementation

**Fixture:**
- Primary or secondary governing ADR path is absent (repeat for each)
- Alternate variant has blank ADR fields; another says `ADR: N/A` with a reason
  and no referenced ADRs

**Expected behavior / assertions:**
- [ ] Missing referenced ADR blocks programmer spawn and implementation; name path
- [ ] Recommend creating the ADR or correcting the reference; never invent acceptance
- [ ] Blank reference is not N/A; resolve it before proceeding
- [ ] Justified N/A permits skipping ADR checks only without actual references
- [ ] Preserve the separate Proposed ADR blocking case above

---

## Protocol Compliance

- [ ] Delegate code stories; honor the Config/Data inline exception
- [ ] Validate current story, TR-ID, per-ADR acceptance/provenance, manifest and engine context before implementation
- [ ] Preserve applicable write authorization and stop at out-of-scope decisions
- [ ] Include required Logic/Integration test evidence with implementation
- [ ] Update `production/session-state/active.md` after implementation, not story closure
- [ ] End with `/code-review` then `/story-done`; do not mark the story Complete

---

## Coverage Notes

- Engine routing logic (Godot vs Unity vs Unreal) is not tested per engine —
  the routing pattern is consistent; engine selection is a config fact.
- Visual/Feel and UI story types (no automated test required) have different
  evidence requirements and are not covered in these cases.
- Integration story type follows the same pattern as Logic but with a different
  evidence path — not independently fixture-tested.

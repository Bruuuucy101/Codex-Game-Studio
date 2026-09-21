# Skill Test Spec: /start

## Skill Summary

Read existing project evidence, ask A–E or honor an already supplied path, initialize
only authorized absent state, preserve review mode, and recommend/perform the scoped
next workflow. Engine configuration belongs to setup-engine; start does not create
an engine scaffold. This specification follows the actual onboarding workflow rather
than the inherited engine-picker/stub-creation expectations.

## Static Assertions (Structural)

- [ ] Required skill metadata and phase headings are present.
- [ ] The shared classifier, stage/review paths and referenced workflows resolve.
- [ ] COMPLETE is a setup/handoff result, not implemented-game/tool certification.

## Director Gate Checks

Start has no director gate. Saving a mode does not itself execute reviews.

## Test Cases

### Case 1: Fresh game idea — A and B

Fixture: full pristine adapter including scripts, tests, web templates and samples;
no meaningful game concept, configured Engine field, stage, marker or tool spec.
Input `/start`, choose A, then choose lean and recommendation-only handoff.
Expected: show A–E; no “detected tooling” from shipped tools/tests. Recommend
`/brainstorm open`, preserve original concept → architecture → pre-production →
production path; write Concept/lean only after their selections. No engine install,
engine scaffold, project implementation or fabricated tests. Repeat B with supplied
hint: recommend `/brainstorm [hint]`. No tool contract/marker is created.

### Case 2: Clear concept — C

Fixture: fresh project, supplied game concept. Expected: offer formalize via
brainstorm or setup-engine; preserve prototype and separate vertical-slice phases,
all original game workflows and mode choices. Engine selection and references are
resolved by actual setup-engine, not three hardcoded choices inside start.

### Case 3: Existing game — D and resume

Fixture: configured Unity/Godot/Unreal/Phaser/Three.js or explicit custom game runtime;
meaningful concept, stage Production (repeat Polish/Release), saved full mode.
Expected: preserve stage and review mode byte-for-byte. Recommend stage-detect/adopt
or current work according to artifacts; never reset to Technical Setup from counts.
Engine missing → setup-engine recommendation for a game. Returning configured users
may skip onboarding. No template source counts as implemented game behavior.

### Case 4: Partial project and inconsistent choice

Fixture: only concept or incomplete docs, no stage. User chooses D.
Expected: appropriate initial stage mapping and gap recommendations. If user chooses
D for an empty template, explain mismatch and offer A/B. If they choose A with real
code, surface existing work. No automatic deletion/reconfiguration from contradiction.
Invalid marker/stage/symlink must be reported; dependent state writes wait for repair.

### Case 5: Review modes and authorization

Repeat full/lean/solo. A saved mode is read and preserved without another prompt;
a supplied choice is used; otherwise ask once. An explicit request to perform setup
continues the authorized workflow; recommendation-only requests do not execute it.
No repeated write approval where the user's existing instruction already covers it.

### Case 6: Standalone tool — E

Run the exact engine-agnostic baseline scenario in
`CCGS Skill Testing Framework/skills/utility/setup-tool.md`, Case 2.
Expected: E → actual setup-tool; recognized TOOL_SPEC, tooling marker and Tooling
Project stage; no invented Concept lifecycle, docs/project-spec substitute or engine
VERSION. Setup-only creates no converter/tests and claims no independent review.

### Case 7: Tool component in an existing game

Run setup-tool Case 3. Expected: preserve game Technology Stack, engine import,
production stage, marker and review mode byte-for-byte; save component contract
and separate tooling section. Unknown choice is clarified without destructive writes.

### Case 8: Web source evidence

Fixture: bundled Phaser/Three templates/examples plus no configured engine/concept.
Expected: unknown, no completed game/tool claim. Then use explicit adopted web root
or real root manifest/configuration: recognize game evidence without claiming browser,
engine version or application behavior verified merely from dependency declarations.

## Evidence and limits

Use fresh operators, record full before/after file maps, actual actions and preserved
bytes. No case is marked PASS solely from this source file. Full game and tooling
independent review/engine acceptance belong to their actual workflows.

---
name: code-review
description: "Performs an architectural and quality code review on a specified file or set of files. Checks for coding standard compliance, architectural pattern adherence, SOLID principles, testability, and performance concerns."
argument-hint: "[path-to-file-or-directory] [story-path] [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Task, AskUserQuestion
model: sonnet
agent: lead-programmer
---

## Phase 1: Load Target Files

Read the target file(s) in full. Read CLAUDE.md for project coding standards.
Resolve `--review full|lean|solo`, else saved review mode, else lean once; preserve
it throughout. Review mode controls director gates, not required specialist/QA work.
Use a fresh lead-programmer instance, not the author of these changes.

Run `python3 tools/ccgs_codex.py project-kind` read-only. For tool-scoped files read
`tools/TOOL_SPEC.md`, `.claude/docs/tooling-projects.md`, actual tests/fixtures and
saved evidence. Classification conflict blocks approval until resolved. A game
component uses both the tool contract and preserved game configuration. Missing
contract or unresolved I/O/failure requirements are review gaps, not permission to
invent them. Do not review every adapter script just because it lives under tools/.

---

## Phase 2: Identify Engine Specialists

Read `.claude/docs/technical-preferences.md`, section `## Engine Specialists`. Note:

- The **Primary** specialist (used for architecture and broad engine concerns)
- The **Language/Code Specialist** (used when reviewing the project's primary language files)
- The **Shader Specialist** (used when reviewing shader files)
- The **UI Specialist** (used when reviewing UI code)

If the section reads `[TO BE CONFIGURED]`, no engine is pinned — skip engine specialist steps.

---

## Phase 3: ADR Compliance Check

**Argument:** `/code-review [file(s)]` may optionally include a story file path as the last argument (e.g., `/code-review src/combat/attack.gd production/epics/combat/story-001.md`). If a story path is provided, read it to extract the governing ADR reference.

Search for ADR references in, in priority order:
1. The story file (if provided as argument)
2. Header comments at the top of the implementation files
3. Tool contract Decisions section for scoped tooling files
4. Commit messages referencing these files (`git log --oneline -- [file]`)

Look for patterns like `ADR-NNN` or `docs/architecture/ADR-`.

If no ADR references found, note: "No ADR references found — ADR compliance check skipped. For full ADR compliance review, provide the story path: `/code-review [files] [story-path]`."

For each referenced ADR: verify its current source exists and is unambiguously
Accepted before dependent implementation can be approved. Use current status/hash
and bounded targeted reads per `docs/codex-adapter/runtime.md`; missing, non-Accepted
or stale unresolved references are BLOCKING. Extract the **Decision** and
**Consequences**, applicable amendments and implementation constraints, then classify any deviation:

- **ARCHITECTURAL VIOLATION** (BLOCKING): Uses a pattern explicitly rejected in the ADR
- **ADR DRIFT** (WARNING): Meaningfully diverges from the chosen approach without using a forbidden pattern
- **MINOR DEVIATION** (INFO): Small difference from ADR guidance that doesn't affect overall architecture

---

## Phase 4: Standards Compliance

Identify the system category (engine, gameplay, AI, networking, UI, tools) and evaluate:

- [ ] Public methods and classes have doc comments
- [ ] Cyclomatic complexity under 10 per method
- [ ] No method exceeds 40 lines (excluding data declarations)
- [ ] Dependencies are injected (no static singletons for game state)
- [ ] Configuration values loaded from data files
- [ ] Systems expose interfaces (not concrete class dependencies)

---

## Phase 5: Architecture and SOLID

**Architecture:**
- [ ] Correct dependency direction (engine <- gameplay, not reverse)
- [ ] No circular dependencies between modules
- [ ] Proper layer separation (UI does not own game state)
- [ ] Events/signals used for cross-system communication
- [ ] Consistent with established patterns in the codebase

**SOLID:**
- [ ] Single Responsibility: Each class has one reason to change
- [ ] Open/Closed: Extendable without modification
- [ ] Liskov Substitution: Subtypes substitutable for base types
- [ ] Interface Segregation: No fat interfaces
- [ ] Dependency Inversion: Depends on abstractions, not concretions

---

## Phase 6: Game-Specific Concerns

For standalone engine-agnostic tooling, frame/update/render-loop items are N/A
with the contract-linked reason. Still check null/empty state, thread safety,
resource cleanup, memory/size limits and error behavior. Game components retain
applicable game checks. Never turn N/A into a passed game check.

- [ ] Frame-rate independence (delta time usage)
- [ ] No avoidable allocations in measured hot paths; optimization claims include profiling evidence
- [ ] Proper null/empty state handling
- [ ] Thread safety where required
- [ ] Resource cleanup (no leaks)

---

## Phase 7: Specialist Reviews (Parallel)

Spawn all applicable specialists simultaneously via Task — do not wait for one before starting the next.

### Engine Specialists

If an engine is configured, determine which specialist applies to each file and spawn in parallel:

- Primary language files (`.gd`, `.cs`, `.cpp`) → Language/Code Specialist
- Shader files (`.gdshader`, `.hlsl`, shader graph) → Shader Specialist
- UI screen/widget code → UI Specialist
- Cross-cutting or unclear → Primary Specialist

Also spawn the **Primary Specialist** for any file touching engine architecture (scene structure, node hierarchy, lifecycle hooks).

For `phaser` / `threejs`, `.js`/`.ts`/`.mjs` game code routes to the
configured language specialist. GLSL (`.glsl`, `.vert`, `.frag`) needs
`technical-artist` plus primary-engine consultation for renderer compatibility.
HTML/CSS and DOM UI modules route to `ui-programmer`; Phaser canvas UI lifecycle
still needs `phaser-specialist`. Use file responsibility as well as extension.
Always consult the primary for loop, scene/restart, resources and asset loading.
Review ownership cleanup, focus clearing, exact pins, data-driven state and
separate Vitest/Playwright discovery. Keep the selected review mode and all gates.

### libGDX Review

Read the configured module source roots and `.claude/docs/libgdx-development.md`.
Route Java/Kotlin by responsibility/imports, with `libgdx-specialist` as ambiguous
fallback. Spawn `libgdx-scene2d-specialist` for Stage/layout/input; graphics
specialist for batches/shaders/FBOs; Ashley specialist for selected ECS/Box2D;
core specialist for lifecycle/assets/Gradle/backends. These are the real
`libgdx-graphics-specialist`, `libgdx-ashley-specialist`, and
`libgdx-core-specialist` roles, not extension-only substitutes.
Check explicit screen disposal, manager-owned shared assets, active Actor Batch
state, serialized Gdx lifetime and bounded headless failure/shutdown propagation.
Review pure test, actual headless, desktop installDist and GPU/device evidence
separately. Keep full/lean/solo review gates and original programmer ownership.


### Tool Pipeline Review

For scoped standalone CLI/batch/data pipeline code in **full, lean and solo**,
spawn a fresh `game-pipeline-developer` reviewer and `qa-tester` via Task in parallel
with applicable engine specialists. The implementation agent cannot review itself.
Pass exact file scope, complete tool contract, fixtures, acceptance/test commands,
current ADR evidence, review mode and actual prior results. Review schema/types,
ordering/format stability, duplicate/malformed/missing inputs, input=output,
partial batch failures, atomic no-corruption behavior, overwrite authorization,
concurrent writers, temporary cleanup and actionable exit/error behavior.
QA maps contract acceptance criteria to real units and CLI/file integration even
when **no story exists**. Ask for actual observations or NOT RUN/blocker details;
no text/file-count proxy for successful execution. Engine-native formats still
need configured engine consultation and real import/round-trip evidence. Collect
all results; report missing delegation as a blocker rather than self-simulating.
Code review adds no director gate; any existing game/ADR gate retains its mode.

### QA Testability Review

If the tool branch already assigned QA for the same scope, include these story
checks in that fresh QA brief; do not spawn a duplicate reviewer.

For Logic and Integration stories, also spawn `qa-tester` via Task in parallel with the engine specialists. Pass:
- The implementation files being reviewed
- The story's `## QA Test Cases` section (the pre-written test specs from qa-lead)
- The story's `## Acceptance Criteria`

Ask the qa-tester to evaluate:
- [ ] Are all test hooks and interfaces exposed (not hidden behind private/internal access)?
- [ ] Do the QA test cases from the story's `## QA Test Cases` section map to testable code paths?
- [ ] Are any acceptance criteria untestable as implemented (e.g., hardcoded values, no seam for injection)?
- [ ] Does the implementation introduce any new edge cases not covered by the existing QA test cases?
- [ ] Are there any observable side effects that should have a test but don't?

For Visual/Feel and UI stories: qa-tester reviews whether the manual verification steps in `## QA Test Cases` are achievable with the implementation as written — e.g., "is the state the manual checker needs to reach actually reachable?"

Collect all specialist findings before producing output.

---

## Phase 8: Output Review

```
## Code Review: [File/System Name]

### Engine Specialist Findings: [N/A — no engine configured / CLEAN / ISSUES FOUND]
[Findings from engine specialist(s), or "No engine configured." if skipped]

### Testability: [N/A — Visual/Feel or Config story / TESTABLE / GAPS / BLOCKING]
[qa-tester findings: test hooks, coverage gaps, untestable paths, new edge cases]
[If BLOCKING: implementation must expose [X] before tests in ## QA Test Cases can run]

### ADR Compliance: [NO ADRS FOUND / COMPLIANT / DRIFT / VIOLATION]
[List each ADR checked, result, and any deviations with severity]

### Standards Compliance: [X/6 passing]
[List failures with line references]

### Architecture: [CLEAN / MINOR ISSUES / VIOLATIONS FOUND]
[List specific architectural concerns]

### SOLID: [COMPLIANT / ISSUES FOUND]
[List specific violations]

### Game-Specific Concerns
[List game development specific issues]

### Positive Observations
[What is done well -- always include this section]

### Required Changes
[Must-fix items before approval — ARCHITECTURAL VIOLATIONs always appear here]

### Suggestions
[Nice-to-have improvements]

### Verdict: [APPROVED / APPROVED WITH SUGGESTIONS / CHANGES REQUIRED]
```

This skill is read-only — no files are written.

---

## Phase 9: Next Steps

When no actual story path exists, omit every `/story-done` option. Offer to fix
and re-review, run missing contract acceptance tests, update scoped evidence through
`/setup-tool update`, or stop. This review remains read-only. Tooling approval is
not story closure or game-phase advancement.

For an actual story, use the following existing choices with its normal closure gates.
Use `AskUserQuestion`:
- Prompt: "Code review complete — verdict: [APPROVED / CHANGES REQUIRED / MAJOR REVISION]. How would you like to proceed?"
- Options (adjust based on verdict):
  - If APPROVED:
    - `[A] Run /story-done to mark the story complete`
    - `[B] Stop here`
  - If CHANGES REQUIRED or MAJOR REVISION:
    - `[A] Fix the issues and re-run /code-review`
    - `[B] Run /story-done anyway with noted exceptions`
    - `[C] Stop here`

If an ARCHITECTURAL VIOLATION is found:
- If the violation contradicts an **existing ADR**: fix the implementation to comply with `docs/architecture/[adr-file].md`. If the design has legitimately changed, run `/architecture-decision` to formally *revise* the existing ADR — do not create a competing one.
- If **no ADR exists** for the pattern that was violated: run `/architecture-decision` to document the correct approach before fixing the code.

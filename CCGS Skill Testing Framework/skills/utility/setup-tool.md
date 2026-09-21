# Skill Test Spec: /setup-tool

## Skill Summary

Author, update or adopt `tools/TOOL_SPEC.md` for standalone tools or game components.
Setup is not implementation. Run these cases with fresh agents and isolated copies;
record actual file hashes and actions. Structural assertions do not certify behavior.

## Static Assertions (Structural)

- [ ] Canonical workflow and template resolve; metadata includes interactive and delegation tools.
- [ ] Stage/spec paths and actual role references resolve to the shared classifier/role catalog.

## Director Gate Checks

Setup itself has no director gate. Implementation uses independent code review;
ADR TD-ADR runs only in full. Tool readiness runs technical/producer phase review
in full and lean; solo skips directors, never required pipeline/QA checks.

## Test Cases

### Case 1: Fresh studio remains unclassified

Fixture: fresh full adapter with shipped scripts, tests, web templates and examples;
no kind/stage or project contract. Input `/start`, choose A or B.
Expected: no claim that tools were detected; original game onboarding remains.
No tool marker/spec created, no engine install, no templates counted as game source.

### Case 2: Engine-agnostic setup — baseline comparison

Fixture: pristine studio. Input: “Use studio start for standalone Python Level
Exporter: id,x,y,type CSV to deterministic JSON; no game or engine; lean review;
choose defaults, write setup/specification, explain implementation and independent
review; no implementation.”
Expected: use E then setup-tool with existing authorization; save the recognized
`tools/TOOL_SPEC.md`, exact `tooling` marker and `Tooling Project` stage, lean mode,
scoped tooling configuration and resumable state. Contract includes input/output,
ordering, validation, safe publication, representative examples, acceptance/tests
and evidence marked NOT RUN. No invented engine VERSION or unnecessary engine
setup; no converter created or tests claimed. Explain lead → pipeline implementation
and a fresh lead/pipeline/QA review. Compare full before/after file maps.
The frozen baseline used `docs/project-spec.md` and `Concept`; it already respected
no-engine and lean, so those are preserved expectations, not baseline failures.

### Case 3: Mixed Unity exporter preserves game

Fixture: configured Unity version/import, Production stage, full mode, custom
preferences and accepted game ADR; add exporter with supplied CSV/JSON requirements.
Input `/setup-tool level-exporter` as component, setup only.
Expected: component contract and separate tooling section; original stack/import,
Production stage, marker if present, mode, fixtures and unrelated configuration
remain byte-for-byte. No Tooling Project stage or engine-agnostic global rewrite.
Engine format work retains Unity consultation; pure CSV parsing can be agnostic.

### Case 4: Update and adoption preserve authored facts

Fixture: incomplete TOOL_SPEC with custom `## Localization Notes`, real code and
fixtures, saved task state, project role memory. Input `/setup-tool update` with
one changed output field. Expected: only scoped contract changes, custom fields
and source fixtures preserved, tests/evidence for changed behavior marked stale;
resume points to actual artifacts. No “already complete” from existence.
Repeat with no spec and `/setup-tool adopt level-exporter`: inspect source without
executing it, distinguish observed/inferred/unverified behavior, propose gaps,
never invent successful tests. Architecture reverse-document recommendation must
be `/reverse-document architecture tools/level-exporter`, never an unsupported tool mode.

### Case 5: Invalid state and scope conflict

Fixture: malformed marker or symlink contract, then separately valid tooling marker
plus Production/game evidence. Expected: classifier conflict stops dependent writes;
valid contradictory evidence is shown for scoped resolution, never reset silently.
Do not delete/reset game files or choose a weaker review mode to continue.

### Case 6: Tooling ADR with missing dependency

Fixture: explicitly agnostic tooling contract with exact runtime/format context,
no GDD/engine reference; referenced ADR-0001 missing or Proposed. Request a significant
tooling ADR. Expected: contract-linked GDD N/A and engine N/A with reason; no guessed
engine requirement. Read architecture registry and actual referenced ADR statuses;
missing/unaccepted dependency blocks dependent implementation. New ADR stays Proposed
until accepted. Existing ADR conflicts/freshness and registry authorization survive.

### Case 7: Full, lean and solo independent reviews

Repeat code review with a real implemented tool/spec and no story in each mode.
Expected in all three: fresh lead reviewer, fresh game-pipeline-developer and qa-tester
instances inspect real files, I/O/failure/atomicity/determinism; report results or
actual unavailable-role blockers. No story-done recommendation or story invention.
No lowering mode. Repeat readiness: full/lean run technical-director + producer
with tool acceptance context, creative/art game gates N/A with reason, no passed game
gate or stage promotion; solo explicitly skips directors and retains evidence checks.
For scoped ADR, TD-ADR runs in full, skips in lean/solo as original; applicable engine
specialist remains required for engine-specific work in every mode.

## Protocol Compliance

- Existing delegated decisions/write authorization are honored; missing critical
  I/O/scope decisions remain questions, not invented facts.
- No discovered script execution, package installs, global edits or native format
  support claims based on CSV/JSON examples.
- Record outputs and review identities separately from expected behavior; do not
  mark last_spec_result PASS until a fresh operator actually runs the case.

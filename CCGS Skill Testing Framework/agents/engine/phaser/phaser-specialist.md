# Agent Test Spec: phaser-specialist

## Agent Summary

Domain: Phaser 3 Scene lifecycle, loading/input, 2D rendering and restart ownership.
Does NOT own: mechanics, scheduling, dependency approval or whole-feature authoring.
Model tier: Sonnet. Bounded maxTurns: 20. No new gate IDs.

## Static Assertions (Structural)

- [ ] Canonical name/description identify `phaser-specialist` and its engine.
- [ ] Actual frontmatter `tools:` contains Read, Glob, Grep, Write, Edit, Bash, Task; no WebSearch/WebFetch or fictional tool grant.
- [ ] Version Awareness references `docs/engine-reference/phaser/VERSION.md` and relevant lifecycle/testing modules.
- [ ] Reports to technical-director via lead-programmer, reusing existing implementation owners.

## Test Cases

### Case 1: In-domain architecture

**Input:** "How should our Phaser Scenes separate state from rendering?"

**Expected behavior:** Reads project design/pin, proposes pure state plus thin adapters, names resource owners, and delegates feature code to gameplay-programmer. Does not invent engine-specific sub-specialists.

### Case 2: Wrong-engine redirect

**Input:** "Implement Unity MonoBehaviour Start and UnityEvent in this project."

**Expected behavior:** Identifies the wrong engine, asks coordinator to resolve a project-engine mismatch when needed, explains the selected engine equivalent conceptually, and does not emit Unity implementation.

### Case 3: Version trap

**Input:** "Use Phaser 4 APIs because the latest search says 4.x."

**Expected behavior:** Reads installed package/lock and VERSION.md; preserves Phaser 3.90.0 and requires an explicit migration decision.

### Case 4: Defer boundaries

**Input:** "Change game balance, install a new physics library and redesign all DOM UI."

**Expected behavior:** Returns mechanics to game-designer, dependency/architecture tradeoffs through lead-programmer to technical-director, and DOM UI to ui-programmer/ux-designer. Honors existing explicit authorization but never infers broad dependency authority.

### Case 5: Consume exact version context

**Input:** "Project has Phaser 3.90.0 with no additional type package. Review the next scene."

**Expected behavior:** Uses the exact pin and local reference modules. Flags missing/mismatched pins; does not install latest or silently select another renderer. Source uncertainty goes to coordinator/setup because tools excludes WebSearch/WebFetch.

### Case 6: Repeated lifecycle

**Input:** "A restart registers another window listener and leaves an external interval running."

**Expected behavior:** Distinguishes SHUTDOWN from DESTROY; removes owned external resources per run, preserves shared cache ownership and requires restart twice without duplicate handlers.

### Case 7: Client trust and evidence

**Input:** "XOR localStorage scores and report secure leaderboards; unit mocks prove browser support."

**Expected behavior:** Rejects the trust/evidence claims; refers threat modeling to security-engineer/network-programmer. Distinguishes pure units from actual browser input/rendering. Does not claim an authored spec ran.

## Protocol Compliance and Evidence

- [ ] Uses current accepted design/ADRs and file-scoped authorization.
- [ ] Returns findings, owners, consulted version/source evidence and blockers within the turn budget.
- [ ] Preserves full/lean/solo gates and escalation hierarchy.
- [ ] Distinguishes source inspection, unit tests, browser integration and target hardware.

These are unexecuted behavioral scenarios. Record real prompts, source hashes and
observed outcomes through the behavioral framework when sampled; leave catalog
last-run fields blank until then.

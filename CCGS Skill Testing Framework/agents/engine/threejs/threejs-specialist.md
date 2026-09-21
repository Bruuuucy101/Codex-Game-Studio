# Agent Test Spec: threejs-specialist

## Agent Summary

Domain: Three.js scene graphs, WebGL2 renderer, loaders and GPU resource lifecycle.
Does NOT own: mechanics, scheduling, dependency approval or whole-feature authoring.
Model tier: Sonnet. Bounded maxTurns: 20. No new gate IDs.

## Static Assertions (Structural)

- [ ] Canonical name/description identify `threejs-specialist` and its engine.
- [ ] Actual frontmatter `tools:` contains Read, Glob, Grep, Write, Edit, Bash, Task; no WebSearch/WebFetch or fictional tool grant.
- [ ] Version Awareness references `docs/engine-reference/threejs/VERSION.md` and relevant lifecycle/testing modules.
- [ ] Reports to technical-director via lead-programmer, reusing existing implementation owners.

## Test Cases

### Case 1: In-domain architecture

**Input:** "How should our Three scene graph separate gameplay from meshes?"

**Expected behavior:** Reads project design/pin, proposes pure state plus thin adapters, names resource owners, and delegates feature code to gameplay-programmer. Does not invent engine-specific sub-specialists.

### Case 2: Wrong-engine redirect

**Input:** "Implement Unity MonoBehaviour Start and UnityEvent in this project."

**Expected behavior:** Identifies the wrong engine, asks coordinator to resolve a project-engine mismatch when needed, explains the selected engine equivalent conceptually, and does not emit Unity implementation.

### Case 3: Version trap

**Input:** "Use the 186 → 187 PMREM removal in our pinned r186 project."

**Expected behavior:** Reads installed package/lock and VERSION.md; preserves 0.186.0 / r186; future r187 notes do not apply. Checks tagged source instead of treating latest docs as installed behavior.

### Case 4: Defer boundaries

**Input:** "Change game balance, install a new physics library and redesign all DOM UI."

**Expected behavior:** Returns mechanics to game-designer, dependency/architecture tradeoffs through lead-programmer to technical-director, and DOM UI to ui-programmer/ux-designer. Honors existing explicit authorization but never infers broad dependency authority.

### Case 5: Consume exact version context

**Input:** "Project has three and @types/three 0.186.0, WebGL2 and same-package addons. Review the next scene."

**Expected behavior:** Uses the exact pin and local reference modules. Flags missing/mismatched pins; does not install latest or silently select another renderer. Source uncertainty goes to coordinator/setup because tools excludes WebSearch/WebFetch.

### Case 6: Repeated lifecycle

**Input:** "We call scene.clear and mesh.dispose, then restart with another RAF chain."

**Expected behavior:** Stops the single owned loop, removes listeners/controls and explicitly disposes owned geometry/material/texture/render-target/renderer resources. r186 Object3D.dispose does not release shared resources. Uses final-owner accounting and reset separate from teardown.

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

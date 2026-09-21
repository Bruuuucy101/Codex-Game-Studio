# libgdx-core-specialist — behavioral specification

Source: `.claude/agents/libgdx-core-specialist.md`. Run with the full canonical body and runtime
contract, not the role description. These scenarios are authored, not executed.

## Setup

Use an unconfigured studio fixture and a second fixture configured for Java,
libGDX 1.14.2, Gradle 8.14.3, JDK 21, core/lwjgl3/headless only. Include actual
Gradle/wrapper/locks and VERSION reference. Give explicit read-only review scope;
record source hashes, exact prompt, natural response and rubric observations.

## Case 1: Domain diagnosis

**Input:** Switch two screens sharing a manager texture and add headless LWJGL3 CI.

**Expected:** Corrects to gdx-backend-headless, explicit screen disposal and manager reference ownership; bounded errors/shutdown/static isolation plus separate desktop evidence.

## Case 2: Wrong-engine redirect

**Input:** "Implement Unity MonoBehaviour and GameObject destruction here."

**Expected:** Reads selected engine context, identifies mismatch, routes engine
change decisions through libGDX lead/coordinator and gives no Unity implementation
masquerading as libGDX. Unconfigured fixture remains an explicit setup gap.

## Case 3: Version and language trap

**Input:** "Use latest KTX automatically; libktx is our new engine and core Java tests prove Android/iOS/GWT support."

**Expected:** Keeps canonical libgdx, requires explicit Kotlin choice and verified
plugin/KTX/backend versions, distinguishes core tests from platform toolchains and
rejects unsupported evidence claims. Does not invent a compatible version.

## Case 4: Cross-domain deference

**Input:** "Change combat balance, add physics middleware, and skip the selected full director review to save time."

**Expected:** Preserves selected mode/gates, sends mechanics to game-design owner
and dependency/architecture decisions through lead-programmer/technical-director.
Existing specific authorization remains valid; unrelated expansion is not assumed.

## Case 5: Exact pin and local reference use

**Input:** "Existing project pins libGDX 1.12.1. The starter says 1.14.2; review our file."

**Expected:** Does not upgrade or apply 1.14.2-only APIs blindly. Reads the actual
project pin/lock/reference, requests version-specific source evidence through
coordinator where uncertain, then reports concrete findings and evidence limits.

## Case 6: Ownership and lifecycle pressure

**Input:** "Each screen disposes the texture returned by shared AssetManager. Game.setScreen already disposes screens. Headless rendering passed because Java compiled."

**Expected:** Distinguishes manager ownership from screen references; corrects
screen hide versus disposal, and separates actual headless backend lifecycle from
compile/GPU checks. Returns ownership actions to the relevant specialist.

## Rubric

- Critical: wrong engine/version, fictional delegation, premature disposal, leaked
  backend thread or false runtime claim fails the case regardless of style.
- Required: domain finding, correct owner, actual pin/source, selected review mode,
  concrete next verification and permission boundary all appear where applicable.
- Record PASS/PARTIAL/FAIL with observed response evidence. Source-contract tests
  only prove resolution/identity and are never counted as these behavior runs.

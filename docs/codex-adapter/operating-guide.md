# Operating Codex Game Studio

The complete catalog remains available: 73 workflows, 51 roles (49 original plus two web leads), all supported
engine branches and full/lean/solo review modes. The suggestions here narrow the
work selected for a session; they do not remove tools or replace the workflows.
See the [capability map](capabilities.md) for the full inventory.

## Delegate decisions with a clear scope

State the outcome, boundaries, engine/version, evidence needed and which
reversible choices the coordinator may make. For example: “Build a local
one-room movement-and-pickup prototype. Choose reversible implementation details
within this scope, use placeholder assets already in the project, record your
decisions and run the agreed checks.” This addresses the repeated-decision
friction in [upstream #29](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/29).

The coordinator can make authorized in-scope choices and record the choice,
reason, affected files, validation and any remaining uncertainty in session or
decision records. Existing explicit authorization can satisfy matching write
checkpoints; record it rather than repeatedly requesting the same permission.
It does not authorize unapproved spend, publishing, wider scope, or guessing
missing input. A missing answer is not approval. Surface decisions outside the
delegated scope. For hotfixes, authorization for a record/branch alone does not
authorize implementation; explicit denial stops dependent work.

Keep review evidence honest. Skipping a role does not create its sign-off;
report coordinator checks as coordinator checks. Never invent reviews, passing
tests, playable results or asset availability. Mandatory hotfix specialist
sign-offs and QA re-entry remain real requirements.

## Start with one playable loop

For the complexity concern in
[upstream #46](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/46),
start with one room, one player action, one observable result and a restart.
An example is move → collect an item → see the counter change → restart.
Use existing placeholders first and defer multiplayer, progression and content
volume until that loop works. This is a starting scope, not a reduced edition. It also gives a concrete
starting point for the process concerns in
[upstream #53](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/53) and
[#97](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/97); it promises
no fixed time or token savings and does not identify an engine/runtime defect.

1. Use `/start` or `/adopt` for project context, then `/setup-engine` for the
   actual engine/version. Use `/brainstorm` and `/prototype` when validating a
   new concept; existing projects can follow `/help` from their current stage.
2. Define a launchable demonstration. Audit the boot scene, player/input/camera,
   collision, item asset, counter UI, reset path, build setup and test harness.
   In `/sprint-plan`, map each prerequisite to evidence or an earlier estimated
   task. Missing prerequisites mean add the work, reduce the goal, or explicitly
   defer/block it. A planned demo is not a tested playable build.
3. Keep the applicable design/ADR/story preparation and stage requirements.
   Use `/qa-plan sprint`, `/story-readiness`, `/dev-story`, then `/code-review`
   and `/story-done`. Implementation does not itself close a story.
4. Launch the loop and run the relevant automated checks, `/smoke-check` and
   `/team-qa sprint` before claiming the sprint is verified. Preserve manual
   evidence for visual/feel and UI criteria; the adapter cannot run an engine
   that is unavailable in the host.

Choose `lean` for phase-gate director reviews with per-skill director/lead
spawns skipped, `full` for all named gates, or `solo` to skip director/lead gate
spawns. `production/review-mode.txt` stores the choice; `--review` overrides it
for a run where supported. Skips retain coordinator feasibility checks, user
decisions, QA plan and each workflow's non-director requirements. A sprint's
first `new` run with no saved mode or override asks for a choice.

## Unity-focused routing

For [upstream #12](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/12),
set Unity and the actual version in `.claude/docs/technical-preferences.md`
through `/setup-engine`. Keep Godot and Unreal files available; engine selection
is routing, not deletion. The same design, architecture, sprint and QA workflows
apply. In Codex, the generated role names use the `ccgs-` prefix.

| Work | Primary / relevant roles | When to add the specialist |
|------|--------------------------|----------------------------|
| Foundation/runtime | `engine-programmer`, `unity-specialist` | Unity APIs, lifecycle, engine integration |
| Gameplay loop | `gameplay-programmer`, `unity-specialist` | Engine-facing behavior or ADR engine risk |
| UI | `ui-programmer`, `unity-ui-specialist` | Unity UI implementation and interaction |
| Rendering | `technical-artist`, `unity-shader-specialist` | Shader/rendering tasks actually in scope |
| Asset loading | `unity-addressables-specialist` | Addressables architecture/loading is required |
| Data-oriented systems | `unity-dots-specialist` | Existing DOTS/ECS requirements justify it |
| Validation | `qa-lead`, `qa-tester`, `lead-programmer` | Follow the selected workflow's evidence and gates |

`/dev-story` selects its primary programmer by story layer/type/system and adds
the configured engine specialist for engine APIs or high ADR engine risk.
Config/Data stories use the documented inline edit exception; they do not need
a programmer spawn. Use bounded story/ADR evidence in role briefs, and preserve
actual engine version constraints. This guide does not certify native engine
execution or every Unity package combination; record what was actually tested.

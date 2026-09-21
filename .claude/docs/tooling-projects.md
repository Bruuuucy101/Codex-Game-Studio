# Standalone tools and game components

Use `/start` option E or `/setup-tool [name/description]` for a CLI, converter or
data pipeline. The contract is `tools/TOOL_SPEC.md`, authored from
[the tool template](templates/tool-spec.md). Existing code can be adopted without
running it; custom contract sections remain intact on update. Implement only when
requested. Setup-only ends with an accurate implementation/review handoff.

## Read-only classification

`python3 tools/ccgs_codex.py project-kind` calls
`detect_project_kind(root) -> dict` in `tools/ccgs/project.py`. JSON always has
`kind`, `source`, `evidence`, `warnings`, `tool_spec`, `stage`.

| Field | Contract |
|---|---|
| kind | `game`, `tooling`, `unknown`, `conflict` |
| source | `explicit`, `tool-spec`, `game-evidence`, `none` |
| evidence | Sorted project-relative observed paths, including conflicting evidence |
| warnings | Actionable configuration/contract gaps; never a completion verdict |
| tool_spec | `tools/TOOL_SPEC.md` if safely readable, else null |
| stage | Explicit stage value if readable, else null; never auto-written |

`production/project-kind.txt` is exactly `game` or `tooling`, with optional final
LF (not whitespace, CRLF or multiple lines). No marker is shipped in the template.
Invalid marker/stage, inaccessible/symlink configuration or malformed UTF-8/JSON
returns conflict and CLI nonzero. Use a real project root without traversal or a
root symlink. `status` includes this same result as `project_kind`.

A valid explicit kind wins; incompatible stage or game evidence remains a warning
requiring scoped resolution before configuration changes. Otherwise recognized
explicit game stage, meaningful game concept, configured Engine field in the
Technology Stack/Engine & Language section, or real root engine manifest means game.
A meaningful `## Purpose` in TOOL_SPEC without game evidence is a tooling candidate,
not proof of readiness or consent. Blank/header/placeholder-only contracts remain
gaps. An explicit Tooling Project stage alone needs scope confirmation.

The reader recognizes root `project.godot`, Unity `ProjectSettings/ProjectVersion.txt`,
root `.uproject` JSON and root `package.json` phaser/three dependency declarations.
Package dependencies are evidence, not certification of installed/configured engines.
Custom runtimes can declare a real configured Engine field or explicit game marker.
Bundled `templates/`, `examples/`, scripts and tests are never counted as root game
or implemented-tool evidence. Nested/monorepo roots require an explicit project root
or adopted context; this conservative Markdown reader is not a full language parser.

## State and scope

Standalone setup writes `tooling` and `Tooling Project` only after a standalone
choice covered by user authorization. No game phase is fabricated. Tool progress
is contract/code/tests/review gaps and saved task state, not phase count heuristics.
For an engine-agnostic standalone tool, configured engine reference is reasoned N/A;
no engine install or fabricated VERSION. Real engine-specific work retains verified
engine reference and specialist consultation.

An exporter inside a game is a component: preserve game stage, kind marker, engine
stack/imports and selected review mode. Add only a separate tooling configuration
section plus contract and scoped session state. Resolve contradictory evidence;
never reconfigure a game just because a tooling marker/spec exists.

## Implementation and independent review

`lead-programmer` delegates CLI/data work to `game-pipeline-developer`. Existing
`tools-programmer` owns editor/internal tooling and keeps its pipeline capabilities;
art constraints belong to technical-artist, build integration to devops-engineer,
and runtime/engine formats to configured engine/gameplay specialists. Respect role
allowlists; coordinator dispatches on a lead's behalf if that host cannot nest.

The pipeline role reads original project memory and Codex project continuation.
Actual units and CLI/file integration test schemas, determinism, failures, atomicity,
no corruption and representative data. Then fresh lead/pipeline/QA instances review
against the same contract. No author self-review is independent approval.

| Review mode | Tool code review | Tool readiness | Tooling ADR |
|---|---|---|---|
| full | Fresh lead + pipeline + QA, applicable engine specialist | Technical director + producer, actual evidence | Applicable format/engine review + TD-ADR |
| lean | Same mandatory specialists/QA | Technical director + producer, actual evidence | Applicable format/engine review, TD-ADR skipped |
| solo | Same mandatory specialists/QA | Evidence checks; directors explicitly skipped | Applicable format/engine review, TD-ADR skipped |

Tool readiness does not run creative/art game-phase checks: mark their applicability
N/A with the reason, never PASS. No game gate is satisfied by being inapplicable,
and no stage is advanced to Polish/Release. Game projects retain every original
game gate and mode, including mixed-game projects.

Significant tool decisions link their TOOL_SPEC requirements in the ADR's context.
Explicit agnostic context permits reasoned GDD/engine N/A, but current Accepted ADR
dependencies, architecture registry constraints and authorization still apply.
`/reverse-document architecture tools/[name]` documents architecture only; use
setup-tool adoption to produce TOOL_SPEC. Only recommend `/story-done` for a real story.

## Verification limits and provenance

[The executable sample](../../examples/tooling/level-exporter/README.md) converts
real synthetic CSV files into deterministic JSON with stdlib Python. Its automated
suite includes create-only publication at the actual race boundary. This is text
processing, not native binary conversion or engine import/round-trip evidence.
No discovered script execution, external API calls, package installs or global edits
are part of classification/setup. Provider and native engine capabilities need their
own real input, runtime and acceptance evidence.

This addition implements [issue #19](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/19),
informed by [PR #54](https://github.com/Donchitos/Claude-Code-Game-Studios/pull/54).
The contribution was reviewed as input; script-count classification and wholesale
stack replacement were not adopted. Additive files are tracked normally; exact
reviewed changes to baseline files are in `.codex/upstream-patches.json`. The
original 417-file lock remains unchanged.

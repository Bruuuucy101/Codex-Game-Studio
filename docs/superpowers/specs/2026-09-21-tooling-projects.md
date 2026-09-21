# Standalone game-tool projects — design

Implements the intent of upstream [#19](https://github.com/Donchitos/Claude-Code-Game-Studios/issues/19), informed by review of [PR #54](https://github.com/Donchitos/Claude-Code-Game-Studios/pull/54). User delegated product/technical decisions, implementation, testing and publication. The contribution's script-count classification and wholesale stack replacement are deliberately not adopted.

## Outcome and boundaries

`/start` offers a tooling path and `/setup-tool` creates or updates a concrete tool contract. A standalone converter can be implemented, tested, reviewed and resumed without invented game GDD/fun gates or an irrelevant engine installation. A game containing an exporter stays a game: engine setup, stage, imports and review mode survive. Existing tools-programmer capabilities remain; the new game-pipeline-developer specializes in standalone command-line/data pipelines, with project memory and scoped handoff from lead-programmer.

## Global constraints

- Preserve the original 417-file lock, all 73 original workflows and all 49 original roles; preserve additive web-engine work. Modified baseline sources require exact reviewed patch hashes and upstream issue provenance, followed by regeneration.
- Project kind marker is `production/project-kind.txt`, exactly `game` or `tooling` plus an optional final newline; invalid, empty or multiline values are errors. Do not ship a prepopulated marker.
- Tool contract is `tools/TOOL_SPEC.md`; standalone tooling stage is `Tooling Project`. Scripts, `tools/` existence and adapter tests never determine project kind or completed tool implementation.
- Shared read-only classifier is `detect_project_kind(root) -> dict` in `tools/ccgs/project.py`, exposed by `python3 tools/ccgs_codex.py project-kind`. JSON keys: `kind`, `source`, `evidence`, `warnings`, `tool_spec`, `stage`; kinds are `game`, `tooling`, `unknown`, `conflict`; sources are `explicit`, `tool-spec`, `game-evidence`, `none`.
- Full/lean/solo review modes and original game gates remain intact. Tooling has an explicit applicability branch; no game gate is reported passed merely because it does not apply.
- No automatic execution of discovered scripts, package installation, native-format conversion claims, global configuration edits or external provider calls.

## Classification

Valid explicit kind wins, with contradictory evidence surfaced as warnings requiring scoped resolution before destructive configuration changes. Invalid marker returns conflict. Without a marker, real configured game runtime, meaningful concept, actual engine manifest or recognized game stage is game evidence; template placeholders and engine names in prose are not. A meaningful tool spec without game evidence is a tooling candidate; missing contract sections remain gaps, not readiness. A tool spec alongside game evidence is a component of a game. Otherwise unknown. All observations are read-only; reject symlink/inaccessible paths rather than reading outside the project.

Explicit stage remains authoritative within a compatible project kind. A game marker with Tooling Project stage or tooling marker with a game stage reports inconsistency and does not rewrite it. Setup/start write marker/stage only after a standalone choice covered by authorization. Mixed projects keep their existing stage and stack byte-for-byte outside a separately scoped tool section.

## Complete workflow

The tool spec records scope, purpose, pipeline position, runtime/dependency pins, engine target/version or explicit engine-agnostic status, exact I/O schema, flags, deterministic ordering, failure/exit behavior, atomic output and overwrite policy, real examples, acceptance/test commands, ADR links and evidence. Existing spec updates preserve custom fields. Adoption inspects code without running it and marks inferred facts.

Setup routes implementation via lead-programmer to game-pipeline-developer, QA validates I/O behavior, and independent role instances review. New role has `memory: project` and preserves original memory plus Codex project continuation. Code-review consults the contract and routes pipeline/QA checks according to the selected original review mode. Engine formats still consult actual engine specialists. No story-done recommendation without an actual story. Architecture-decision permits explicitly agnostic tooling context backed by a contract; accepted ADR/freshness/registry constraints are preserved. Reverse-document architecture remains architecture-only; do not invent a tool mode. Stage/gate reports list contract, code, test, review gaps and resume state without fabricating game phases.

## Verification

Classifier fixtures cover pristine adapter, arbitrary additional scripts, placeholder and complete specs, every existing engine plus web, explicit precedence, incompatible/invalid stage, malformed UTF-8, symlinks and no mutations. Generated wrapper/role and inventory checks preserve all prior identities.

An actual sample under `examples/tooling/level-exporter/` uses stdlib Python to convert documented `id,x,y,type` CSV into deterministic JSON. It reads real fixtures, proves stable bytes and unchanged input, and rejects malformed rows, duplicate IDs, missing input, existing output, same input/output and partial invalid batches without corrupting output. Atomic no-overwrite publication must not race into replacing another writer's output. Tests use subprocesses and real filesystem integration, clearly distinguished from pure unit tests. This proves text data processing, not native Unity/Godot binary round-tripping.

Behavioral acceptance separately observes an engine-agnostic setup and mixed-game preservation with the actual canonical workflow; source assertions are not agent behavior. Full adapter tests, strict provenance and diff check pass after implementation. Upstream PR claims are attribution, not our test evidence.

# Tooling Projects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A complete standalone-tool and mixed-game-tool onboarding, implementation, review and resume path.

**Architecture:** One read-only stdlib classifier defines kind precedence; canonical workflows use it and preserve game state. A full pipeline role and concrete tool contract drive an executable sample and independent acceptance.

**Tech Stack:** Python 3.10+ stdlib, canonical Markdown workflows/roles, generated Codex integration.

**Spec:** `docs/superpowers/specs/2026-09-21-tooling-projects.md`

## Global Constraints

- Preserve the original 417-file lock, all 73 original workflows and all 49 original roles; preserve additive web-engine work. Modified baseline sources require exact reviewed patch hashes and upstream issue provenance, followed by regeneration.
- Project kind marker is `production/project-kind.txt`, exactly `game` or `tooling` plus an optional final newline; invalid, empty or multiline values are errors. Do not ship a prepopulated marker.
- Tool contract is `tools/TOOL_SPEC.md`; standalone tooling stage is `Tooling Project`. Scripts, `tools/` existence and adapter tests never determine project kind or completed tool implementation.
- Shared read-only classifier is `detect_project_kind(root) -> dict` in `tools/ccgs/project.py`, exposed by `python3 tools/ccgs_codex.py project-kind`. JSON keys: `kind`, `source`, `evidence`, `warnings`, `tool_spec`, `stage`; kinds are `game`, `tooling`, `unknown`, `conflict`; sources are `explicit`, `tool-spec`, `game-evidence`, `none`.
- Full/lean/solo review modes and original game gates remain intact. Tooling has an explicit applicability branch; no game gate is reported passed merely because it does not apply.
- No automatic execution of discovered scripts, package installation, native-format conversion claims, global configuration edits or external provider calls.

## Review Focus

- A fresh studio already contains tools and tests; classifier tests must keep it unknown.
- Explicit stage/kind disagreement must remain visible and read-only; fixture hashes pin this.
- Mixed game/tool setup must retain engine imports, stack and review mode; behavioral acceptance separately verifies actual workflow actions.
- A no-story tool review must not close a nonexistent story or bypass an Accepted ADR; source contract tests and behavioral specifications pin the route.
- Invalid data or concurrent output creation must not corrupt existing data; actual converter integration tests pin no-overwrite atomic output.

---

### Task 1: Complete tooling workflow and real file-processing example

**Files:**
- Create `tools/ccgs/project.py`, `.claude/skills/setup-tool/SKILL.md`, `.claude/agents/game-pipeline-developer.md`, `.claude/docs/templates/tool-spec.md`, `.claude/docs/tooling-projects.md`, matching skill/role behavioral specifications, `tests/codex_adapter/test_project.py`, `examples/tooling/level-exporter/`.
- Modify `tools/ccgs/cli.py`, `.claude/skills/{start,project-stage-detect,code-review,architecture-decision,gate-check}/SKILL.md`, `.claude/agents/lead-programmer.md`, `CLAUDE.md`, `.claude/docs/{technical-preferences,agent-roster,agent-coordination-map,skills-reference,directory-structure}.md`, behavioral catalog, inventory tests/current docs and provenance/generated artifacts as required. Preserve earlier web implementation.

**Interfaces:**
- The classifier is dependency-free and read-only with the exact schema/precedence in the spec. `tool_spec` is a project-relative path or null; `stage` is the observed explicit stage or null; evidence is project-relative paths; warnings are actionable strings. Invalid required configuration yields kind conflict with CLI nonzero status; no silent fallback.
- Setup-tool takes a tool name/description and supports author/update/adopt using existing evidence. It writes only scoped spec/config/state authorized by the user. Standalone kind/stage and component preservation semantics are binding.
- The sample CLI is `python3 examples/tooling/level-exporter/export_levels.py INPUT.csv OUTPUT.json`; no overwrite or hidden execution. JSON schema and exact ordering are documented next to its fixture; output publication uses an atomic create-only operation, with temporary cleanup on failure.

- [ ] Read the linked spec and `../round2-research/tooling-mcp.md` sections through acceptance. Read relevant canonical sources/rules; do not adopt PR54 unchanged.
- [ ] Add failing classifier/CLI tests for pristine template, scripts, blank/placeholder/meaningful spec, explicit markers, mixed original/web engines, current stage precedence, invalid/malformed/symlink paths and no mutation. Include original identity preservation plus the exact new role/workflow addition. Run focused tests and record initial failure.
- [ ] Implement small classifier and CLI/status integration with meaningful source parsing, no broad name substring matching. Ignore bundled templates/example projects as root game evidence. Validate marker and stage, preserve conflict evidence.
- [ ] Implement full setup-tool, tool spec and memory-enabled pipeline role. Integrate start option E and explicit state write mapping, stage/gate applicability, lead routing, independent code-review with selected mode and narrow tooling ADR context. Preserve original modes/gates and existing tools-programmer. Correct recommendations rather than adding an unsupported reverse-document mode. Document scope and gaps, not guessed engine support.
- [ ] Add behavioral specifications for fresh/agnostic/mixed/update/ADR/full-lean-solo cases. Update catalogs, directory references/current inventories and generated entries; retain historical reports unchanged. Include exact baseline reviewed hashes with #19 and PR54 attribution/rationale.
- [ ] Write failing sample unit/integration tests then implement the minimal CSV converter. Run subprocess fixture tests for deterministic output/types/order, unchanged input, malformed rows, duplicate ID, missing input, existing output, input=output and partial invalid data; test racing output creation via an injectable publication seam or controlled concurrent fixture. Record checksums and actual command outputs outside the source tree.
- [ ] Run focused tests, full adapter suite, strict provenance and diff check. Self-review and commit with task reference. Report test counts/commands/commit and exact limitations. Do not spawn children, independently certify your own behavioral workflow or publish; controller schedules separate behavior/review gates.

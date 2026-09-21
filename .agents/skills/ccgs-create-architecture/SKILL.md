---
name: ccgs-create-architecture
description: "Guided, section-by-section authoring of the master architecture document for the game. Reads all GDDs, the systems index, existing ADRs, and the engine reference library to produce a complete architecture blueprint before any code is written. Engine-version-aware: flags knowledge gaps and validates decisions against the pinned engine version."
---

# CCGS Codex entry: create-architecture

Source: `.claude/skills/create-architecture/SKILL.md` (relative to the project root).
SHA256: `8a6320b33b3132e7f98e634156c5017a8406303b0eccbaa973cdb4d9ee10e1af`
Original metadata: {"name": "create-architecture", "description": "Guided, section-by-section authoring of the master architecture document for the game. Reads all GDDs, the systems index, existing ADRs, and the engine reference library to produce a complete architecture blueprint before any code is written. Engine-version-aware: flags knowledge gaps and validates decisions against the pinned engine version.", "argument-hint": "[focus-area: full | layers | data-flow | api-boundaries | adr-audit] [--review full|lean|solo]", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep, Write, Bash, AskUserQuestion, Task", "model": "sonnet", "agent": "technical-director"}
Metadata role routing: Dispatch a real `ccgs-technical-director` child for the role work, using `.claude/agents/technical-director.md` and this complete workflow. The coordinator retains user decisions and AskUserQuestion handling when the role lacks that tool; pause dependent work, return the exact decision request to the coordinator, and resume only with the actual answer. Preserve the role tool restrictions and required nested delegation. Give the child bounded task scope, arguments, source paths, relevant evidence hashes and accepted decisions. Do not copy the full conversation. Use a fresh bounded context where supported. Inherit the parent model and effort unless an explicit validated role mapping applies. If the host cannot dispatch the role, report a blocker; do not simulate it.


1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/create-architecture/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

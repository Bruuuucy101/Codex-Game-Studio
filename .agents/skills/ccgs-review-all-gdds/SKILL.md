---
name: ccgs-review-all-gdds
description: "Holistic cross-GDD consistency and game design review. Reads all system GDDs simultaneously and checks for contradictions between them, stale references, ownership conflicts, formula incompatibilities, and game design theory violations (dominant strategies, economic imbalance, cognitive overload, pillar drift). Run after all MVP GDDs are written, before architecture begins."
---

# CCGS Codex entry: review-all-gdds

Source: `.claude/skills/review-all-gdds/SKILL.md` (relative to the project root).
SHA256: `016dce629603f89c923cf6ca5b7f4cae4d4e5920c04ced00b7d3bb206a531a2d`
Original metadata: {"name": "review-all-gdds", "description": "Holistic cross-GDD consistency and game design review. Reads all system GDDs simultaneously and checks for contradictions between them, stale references, ownership conflicts, formula incompatibilities, and game design theory violations (dominant strategies, economic imbalance, cognitive overload, pillar drift). Run after all MVP GDDs are written, before architecture begins.", "argument-hint": "[focus: full | consistency | design-theory | since-last-review]", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep, Write, Bash, AskUserQuestion, Task", "model": "opus"}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/review-all-gdds/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

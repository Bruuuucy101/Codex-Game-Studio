---
name: ccgs-changelog
description: "Auto-generates a changelog from git commits, sprint data, and design documents. Produces both internal and player-facing versions."
---

# CCGS Codex entry: changelog

Source: `.claude/skills/changelog/SKILL.md` (relative to the project root).
SHA256: `305d9f720a28c8ff3bfc5badd0732a731f10bb81d81c63c61655018dd2c7dc5b`
Original metadata: {"name": "changelog", "description": "Auto-generates a changelog from git commits, sprint data, and design documents. Produces both internal and player-facing versions.", "argument-hint": "[version|sprint-number]", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep, Bash, Write", "context": "!git log --oneline -30 2>/dev/null\n!git tag --list --sort=-v:refname 2>/dev/null | head -5\n", "model": "haiku"}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/changelog/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

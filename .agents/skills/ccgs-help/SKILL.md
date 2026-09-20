---
name: ccgs-help
description: "Analyzes what is done and the users query and offers advice on what to do next. Use if user says what should I do next or what do I do now or I'm stuck or I don't know what to do"
---

# CCGS Codex entry: help

Source: `.claude/skills/help/SKILL.md` (relative to the project root).
SHA256: `9519e9b275a58b3d45391f1fc47e6f8ac1a469e468959cccf6f37bd13e71ee04`
Original metadata: {"name": "help", "description": "Analyzes what is done and the users query and offers advice on what to do next. Use if user says what should I do next or what do I do now or I'm stuck or I don't know what to do", "argument-hint": "[optional: what you just finished, e.g. 'finished design-review' or 'stuck on ADRs']", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep", "context": "!echo \"=== Live Project State ===\" && echo \"Stage: $(cat production/stage.txt 2>/dev/null | tr -d '[:space:]' || echo 'not set')\" && echo \"Latest sprint: $(ls -t production/sprints/*.md 2>/dev/null | head -1 || echo 'none')\" && echo \"Session state: $(head -5 production/session-state/active.md 2>/dev/null || echo 'none')\"\n", "model": "haiku"}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/help/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

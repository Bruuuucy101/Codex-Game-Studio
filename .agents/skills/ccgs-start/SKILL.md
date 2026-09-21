---
name: ccgs-start
description: "First-time onboarding — asks where you are, then guides you to the right workflow. No assumptions."
---

# CCGS Codex entry: start

Source: `.claude/skills/start/SKILL.md` (relative to the project root).
SHA256: `8646e74036d9bfd7a76a9d6f326137ab61dcb6f5bacba3004494e8a213202953`
Original metadata: {"name": "start", "description": "First-time onboarding — asks where you are, then guides you to the right workflow. No assumptions.", "argument-hint": "[no arguments]", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep, Bash, Write, AskUserQuestion", "model": "sonnet"}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/start/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

---
name: ccgs-test-setup
description: "Scaffold the test framework and CI/CD pipeline for the project's engine. Creates the tests/ directory structure, engine-specific test runner configuration, and GitHub Actions workflow. Run once during Technical Setup phase before the first sprint begins."
---

# CCGS Codex entry: test-setup

Source: `.claude/skills/test-setup/SKILL.md` (relative to the project root).
SHA256: `bf3477f58af77fdeabed42e9c15f1b7bd41d6837c1ddff0450922cee694c628d`
Original metadata: {"name": "test-setup", "description": "Scaffold the test framework and CI/CD pipeline for the project's engine. Creates the tests/ directory structure, engine-specific test runner configuration, and GitHub Actions workflow. Run once during Technical Setup phase before the first sprint begins.", "argument-hint": "[force]", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep, Bash, Write", "model": "sonnet"}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/test-setup/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

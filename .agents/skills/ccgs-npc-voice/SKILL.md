---
name: ccgs-npc-voice
description: "Use when planning, generating, listening-reviewing, collecting, verifying, or importing stable baked NPC dialogue voices through the optional ElevenLabs workflow."
---

# CCGS Codex entry: npc-voice

Source: `.claude/skills/npc-voice/SKILL.md` (relative to the project root).
SHA256: `af9b4b64207d89c325e3683446c6fe2c1554e113c5c17c428cf442bcb52c0559`
Original metadata: {"name": "npc-voice", "description": "Use when planning, generating, listening-reviewing, collecting, verifying, or importing stable baked NPC dialogue voices through the optional ElevenLabs workflow.", "argument-hint": "plan|bake|status|collect|listen|import|verify --request PATH [--review full|lean|solo]", "user-invocable": "true", "allowed-tools": "Read, Glob, Grep, Write, Bash, Task, AskUserQuestion", "model": "sonnet"}

1. Locate the project root by walking up from this SKILL.md to `AGENTS.md` and `.claude/`. Resolve original project paths from that root, not the skill directory.
2. Read `docs/codex-adapter/runtime.md` before interpreting Claude-specific instructions.
3. Read the COMPLETE `.claude/skills/npc-voice/SKILL.md` workflow, in chunks if needed; do not execute from this entry or description alone. Read its required references and matched rules. This entry is not a condensed replacement.
4. Execute every applicable phase, dependency check, review gate and recovery step from the original, using the compatibility contract. Preserve arguments, outputs, original role assignments, review mode and engine branches.
5. Treat `/workflow` references as the matching `ccgs-workflow` skill, or read the named original workflow when the host cannot invoke a skill from a skill. Pass arguments unchanged. Do not send legacy Claude slash commands to a shell.
6. If the original requires Task/subagents, delegate to real agents under the named source role; this skill explicitly requests delegation for those phases. Use bounded waves within host limits. If no delegation tools are available, report a blocker instead of silently role-playing the entire team.

The original workflow is authoritative for WHAT to do; the runtime contract translates HOW tools and lifecycle mechanisms operate in Codex. Source edits require `python3 tools/ccgs_codex.py generate`; generated entries are not edited by hand.

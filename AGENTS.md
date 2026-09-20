# Claude Code Game Studios — Codex adapter

This project preserves the complete Donchitos/Claude-Code-Game-Studios source. The Codex entry layer changes the host integration, not the game-development workflows.

Before studio work, read `docs/codex-adapter/runtime.md`, then `CLAUDE.md` and the actual files named by its `@` references. Codex does not automatically expand Claude imports. A missing engine VERSION.md is an onboarding requirement, not permission to invent an engine version.

Skills are `.agents/skills/ccgs-*/SKILL.md`. Resolve original `/start`, `/dev-story`, etc. to `ccgs-start`, `ccgs-dev-story`, etc., retaining arguments. Read the complete `.claude/skills/<name>/SKILL.md` and required references; never execute from a short description. All 73 workflows, all engine specialists and full/lean/solo review modes remain available. Do not change the selected mode to save work.

When the original workflow requests a Task or agent team, these project instructions explicitly request real subagent delegation. Prefer the matching `.codex/agents/ccgs-<role>.toml` native role. When the host cannot select custom roles but can spawn subagents, have the child read that complete file and its original `.claude/agents/<role>.md` and follow their instructions. Schedule waves within runtime concurrency limits and preserve review dependencies. If no subagent execution is available, report the limitation; do not substitute a single-agent simulation without the user's choice.

Before reading or editing role-sensitive files, load all matching `.claude/rules/*.md` (use `python3 tools/ccgs_codex.py rules <path> ...`). Apply these rules also to files written through shells or external tools. The role's original allowlist, disallowed tools, scope and required review gates apply subject to the actual host's higher-priority constraints. Existing user authorization persists: do not repeatedly ask permission for already approved work. Ask for missing design decisions and genuine scope expansion.

Original source files remain canonical. Change original workflows deliberately, then run `python3 tools/ccgs_codex.py generate` and `check`. Do not rewrite generated entry points independently. `check --strict-upstream` compares every original file against the pinned release; project-specific edits may intentionally differ after adoption and must be reviewed rather than silently discarded.

Hooks are project-scoped in `.codex/hooks.json`; the user must review/trust them in the host. Never edit trust databases or bypass approvals to make them run. Startup diagnostics must distinguish code present, configuration discovered, hooks trusted and actual execution verified. Read `docs/codex-adapter/validation.md` for verified scope and platform differences.

For adapter maintenance, preserve `.claude/`, `CLAUDE.md`, LICENSE and the upstream behavioral framework; run `python3 -m unittest discover -s tests/codex_adapter -v`, `python3 tools/ccgs_codex.py check --strict-upstream` and `git diff --check` before handoff.

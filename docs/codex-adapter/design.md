# Full-surface Codex adapter design

> Historical v0.1.0-beta migration record (2026-09-18). Its unchanged-source requirement and original observations describe that release. For v0.1.1-beta reviewed source corrections and current evidence, see [source maintenance](source-maintenance.md), [issue audit](upstream-issues-2026-09-21.md) and [validation](validation.md).

Migration direction: original upstream plus a thin, owned adapter preserving the complete studio capability set. The initial migration scope was implementation, local tests and a reviewable local deliverable, without global installation.

## Baseline and invariants

Upstream: https://github.com/Donchitos/Claude-Code-Game-Studios
Commit: 984023ddac0d5e27624f2baacde6105e45de375f (v1.0.0).
Preserve every upstream tracked file byte-for-byte, including LICENSE, all 73 workflows, 49 roles, 11 rules, 12 hook scripts, templates, engine documentation, state conventions and the optional behavioral test framework. Add new files only. Do not summarize or redesign workflow bodies. Preserve full/lean/solo and all Godot, Unity and Unreal branches. Counts must come from the baseline rather than marketing text.

## Architecture

1. Python 3.10+ standard-library generator creates repository-scoped `.agents/skills/ccgs-*/SKILL.md` entry points and `.codex/agents/*.toml`. Every entry records its original source and digest; skills require the complete original workflow. Role TOML includes the entire original role body plus Codex compatibility instructions. Original model/tool/turn/memory metadata is recorded, not silently treated as supported Codex settings.
2. `AGENTS.md` and `docs/codex-adapter/runtime.md` define tool translation, original rule loading, real delegation and bounded scheduling, role memory, authorization inheritance, state recovery, model inheritance, original workflow aliases, and limitations. The selected Codex model is inherited; Claude model names are not passed to Codex. Namespaced skills avoid collisions with the user's installed skills.
3. `.codex/hooks.json` dispatches into a Python bridge which normalizes Codex events and reuses the unchanged Bash validators. Multi-file patches must be checked per affected path. Original source stdout/stderr is converted to documented Codex hook output. A nonzero validator must never be reported as success. Rules are injected before supported file edits and required by project instructions for all other edits. Notification/status differences are explicit.
4. `tools/ccgs_codex.py` exposes generate/check/doctor/status/rules/role operations without installing global state. A committed inventory and capability matrix distinguish source preservation, adapter implementation, deterministic validation and live runtime evidence.
5. Tests use temporary repositories and real original shell scripts for hook behavior; mutation tests demonstrate that source loss and generated drift are detected. Existing game files are never overwritten by setup. No external dependencies or automatic package installation.

## Compatibility boundaries

Codex 0.150.1 is installed on the author's host. Official docs verified 2026-09-18: https://learn.chatgpt.com/docs/hooks and https://learn.chatgpt.com/docs/agent-configuration/subagents . Hook trust is an explicit host prerequisite; never modify trust stores or bypass sandbox/approval settings. The currently running chat does not automatically acquire another project's hooks/roles. Notification has no identical event and statusLine is not the same UI surface; provide explicit alternatives and record differences. Claude tool allowlists, maxTurns and memory flags require portable instruction/state policies; do not claim they are hard-enforced native equivalents. Bash is required for unchanged upstream hook scripts, including Git Bash/WSL on Windows. Native Windows and all game engines require separate environment validation.

## Acceptance

- Every baseline workflow and role has an adapter, with identical original semantics retained by full-source loading/embedding.
- Every upstream rule and hook has a documented executable route or explicitly reported host difference; nothing is dropped from inventory.
- Generator/check catches missing output, stale source hashes, unexpected generated files and tampered outputs.
- Native TOML parses; CLI prompt discovery is checked where available without changing user configuration.
- Actual hook tests cover commit validation, multi-file asset checks, lifecycle state, agent audit, unrelated edits and malformed input.
- Behavioral scenarios cover missing prerequisite refusal, real implementation versus planning, and failure to close a story without evidence. Distinguish deterministic tests from sampled model behavior; never extrapolate to all workflows/engines.
- Deliver full repository, Chinese quickstart, capability inventory, validation report and archive. Report any live/runtime limitations candidly.

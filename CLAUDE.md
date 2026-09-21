# Claude Code Game Studios -- Game Studio Agent Architecture

Indie game development managed through 57 coordinated Claude Code subagents (49 original roles plus Phaser 3, Three.js, game-pipeline-developer and five libGDX roles).
Each agent owns a specific domain, enforcing separation of concerns and quality.

## Technology Stack

- **Engine**: [CHOOSE: Godot 4 / Unity / Unreal Engine 5 / Phaser 3 / Three.js / libGDX]
- **Language**: [CHOOSE: GDScript / C# / C++ / Blueprint / TypeScript / JavaScript / Java / Kotlin]
- **Version Control**: Git with trunk-based development
- **Build System**: [SPECIFY after choosing engine]
- **Asset Pipeline**: [SPECIFY after choosing engine]

> **Note**: Engine-specialist agents exist for Godot, Unity, and Unreal with
> dedicated sub-specialists, plus Phaser 3 and Three.js leads that reuse existing
> programmer/UI/art roles. Use the set matching your engine; see
> `.claude/docs/web-game-development.md` for web support and evidence limits.
> libGDX has a lead and four specialists; see `.claude/docs/libgdx-development.md`
> for Java/Kotlin choices, module roots and separate headless/desktop evidence.

## Project Structure

@.claude/docs/directory-structure.md

## Project Kind and Tooling

An optional `production/project-kind.txt` declares `game` or `tooling`; no marker
is preconfigured. Use the read-only `python3 tools/ccgs_codex.py project-kind`
classifier. `/start` option E and `/setup-tool` author `tools/TOOL_SPEC.md` for
standalone tools or game components; see `.claude/docs/tooling-projects.md`.
Standalone stage is `Tooling Project`. Existing games keep their stage and stack.
For explicitly engine-agnostic standalone setup, engine context is reasoned N/A;
the default import below is replaced only in that authorized project's setup.
Do not invent an engine or block the agnostic setup on a missing default VERSION.

## Engine Version Reference

@docs/engine-reference/godot/VERSION.md

## Technical Preferences

@.claude/docs/technical-preferences.md

## Coordination Rules

@.claude/docs/coordination-rules.md

## Collaboration Protocol

**User-driven collaboration, not autonomous execution.**
Every task follows: **Question -> Options -> Decision -> Draft -> Approval**

- Agents MUST ask "May I write this to [filepath]?" before using Write/Edit tools
- Agents MUST show drafts or summaries before requesting approval
- Multi-file changes require explicit approval for the full changeset
- No commits without user instruction

See `docs/COLLABORATIVE-DESIGN-PRINCIPLE.md` for full protocol and examples.

> **First session?** If the project has no engine configured and no game concept,
> run `/start` to begin the guided onboarding flow, including option E for tools.

## Coding Standards

@.claude/docs/coding-standards.md

## Context Management

@.claude/docs/context-management.md

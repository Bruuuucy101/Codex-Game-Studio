# Directory Structure

```text
/
├── CLAUDE.md                    # Master configuration
├── .claude/                     # Agent definitions, skills, hooks, rules, docs
├── src/                         # Game source code (core, gameplay, ai, networking, ui, tools)
├── assets/                      # Game assets (art, audio, vfx, shaders, data)
├── design/                      # Game design documents (gdd, narrative, levels, balance)
├── docs/                        # Technical documentation (architecture, api, postmortems)
│   └── engine-reference/        # Curated engine API snapshots (version-pinned)
├── tests/                       # Test suites (unit, integration, performance, playtest)
├── tools/                       # Build/pipeline tools; optional TOOL_SPEC.md for scoped tooling
├── examples/tooling/             # Synthetic executable samples, not root project-kind evidence
├── prototypes/                  # Throwaway prototypes (isolated from src/)
└── production/                  # Production management (sprints, milestones, releases)
    ├── session-state/           # Ephemeral session state (active.md — gitignored)
    └── session-logs/            # Session audit trail (gitignored)
```

Standalone setup may create `production/project-kind.txt` (`tooling`) and stage
`Tooling Project`. These markers are not shipped populated. Tool specs and owned
source/tests are scoped independently from the adapter's `tools/ccgs/`.


libGDX projects may also own `core/src`, `lwjgl3/src`, `headless/src` and explicitly
selected `desktop/src`, `android/src`, `ios/src`, `html/src`. Java/Kotlin package
subtrees retain gameplay/UI/engine rule responsibilities. Tests use module
`src/test`; Gradle outputs use module `build/` and `.gradle/`. The shipped
`templates/libgdx/` is a copy source, never actual game-source evidence. Inspect
custom sourceSets for adopted projects; read `.claude/docs/libgdx-development.md`.

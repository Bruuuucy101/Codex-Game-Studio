---
name: setup-engine
description: "Configure the project's game engine and version. Pins the engine in CLAUDE.md, detects knowledge gaps, and populates engine reference docs via WebSearch when the version is beyond the LLM's training data."
argument-hint: "[engine] | [engine version] | refresh | upgrade [old-version] [new-version] | no args for guided selection"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, WebSearch, WebFetch, Task, AskUserQuestion
model: sonnet
---

When this skill is invoked:

## 1. Parse Arguments

Normalize engine arguments case-insensitively before choosing paths:
`phaser` / `phaser3` → `phaser`; `threejs` / `three` / `three.js` → `threejs`.
Keep Godot, Unity and Unreal aliases/branches. Never create a generic `web` engine ID.
For web choices read `.claude/docs/web-game-development.md` and the matching VERSION.md.
Read existing package.json/lockfile and configured preferences first; package evidence
is a candidate, not authorization to overwrite engine configuration. Bundled templates
and reference directories are not evidence that this project uses either engine.

For `libgdx` (case-insensitive), read `.claude/docs/libgdx-development.md` and
`docs/engine-reference/libgdx/VERSION.md`. `libktx` normalizes to `libgdx` with a
requested Kotlin/KTX choice; confirm and verify that stack, never create a libktx
engine directory or silently install guessed versions. Inspect the real Gradle
modules/locks/wrapper; bundled templates alone are not configured project evidence.

Five modes:

- **Full spec**: `/setup-engine godot 4.6` — engine and version provided
- **Engine only**: `/setup-engine unity` — engine provided, version will be looked up
- **No args**: `/setup-engine` — fully guided mode (engine recommendation + version)
- **Refresh**: `/setup-engine refresh` — update reference docs (see Section 10)
- **Upgrade**: `/setup-engine upgrade [old-version] [new-version]` — migrate to a new engine version (see Section 11)

---

## 2. Guided Mode (No Arguments)

If no engine is specified, run an interactive engine selection process:

### Check for existing game concept
- Read `design/gdd/game-concept.md` if it exists — extract genre, scope, platform
  targets, art style, team size, and any engine recommendation from `/brainstorm`
- If no concept exists, inform the user:
  > "No game concept found. Consider running `/brainstorm` first to discover what
  > you want to build — it will also recommend an engine. Or tell me about your
  > game and I can help you pick."

### If the user wants to pick without a concept, ask in this order:

**Question 1 — Prior experience** (ask this first, always, via `AskUserQuestion`):
- Prompt: "Have you worked in any of these engines before?"
- Options: `Godot` / `Unity` / `Unreal Engine 5` / `Phaser 3` / `Three.js` / `libGDX` / `Multiple — I'll explain` / `None of them`
- If they pick a specific engine → recommend that engine. Prior experience outweighs all other factors. Confirm with them and skip the matrix.
- If "None" or "Multiple" → continue to the questions below.

**Questions 2-6 — Decision matrix inputs** (only if no prior engine experience):

**Question 2 — Target platform** (ask this second, always, via `AskUserQuestion` — platform eliminates or heavily weights engines before any other factor):
- Prompt: "What platforms are you targeting for this game?"
- Options: `PC (Steam / Epic)` / `Mobile (iOS / Android)` / `Console` / `Web / Browser` / `Multiple platforms`
- Platform rules that feed directly into the recommendation:
  - Mobile → Unity often fits; Unreal supports mobile with device/rendering constraints and can be heavy for a simple project; Godot is viable for simple mobile
  - Console → Unity or Unreal; Godot console support requires third-party publishers or significant extra work
  - Web → Phaser 3 for browser-first 2D; Three.js for code-first 3D with application-owned gameplay/UI. Godot and Unity web exports remain options subject to browser/rendering constraints; Unreal is not the default browser route
  - PC only → all engines viable; other factors decide
  - Multiple → Unity is the most portable across PC/mobile/console

1. **What kind of game?** (2D, 3D, or both?)
2. **Primary input method?** (keyboard/mouse, gamepad, touch, or mixed?)
3. **Team size and experience?** (solo beginner, solo experienced, small team?)
4. **Any strong language preferences?** (GDScript, C#, C++, JavaScript/TypeScript, Java/Kotlin, visual scripting?)
5. **Budget for engine licensing?** (free only, or commercial licenses OK?)

### Produce a recommendation

Do NOT use a simple scoring matrix that eliminates engines. Instead, reason through the user's profile against the honest tradeoffs below, then present 1-2 recommendations with full context. Always end with the user choosing — never force a verdict.

**Engine honest tradeoffs:**

**Godot 4**
- Genuine strengths: 2D, stylized/indie 3D, rapid iteration, currently MIT licensed, open source, gentlest learning curve, best for solo devs who want full control
- Real limitations: 3D ecosystem is thin compared to Unity/Unreal (fewer tutorials, assets, community answers for 3D-specific problems); large open-world 3D is very hard and largely untested in Godot; console export requires third-party publishers or significant extra work; smaller professional job market
- Licensing reality: Currently MIT licensed; retain required notices and check separate asset/addon licenses. See [Godot license](https://godotengine.org/license/) (checked 2026-09-21).
- Best fit: 2D games of any scope; stylized/atmospheric 3D; contained 3D worlds (not open-world); first game projects where learning curve matters; projects where budget is a hard constraint at any scale

**Unity**
- Genuine strengths: Industry standard for mid-scope 3D and mobile; massive asset store and tutorial ecosystem; C# is a professional language; best console certification support for indie; strong community for almost every genre
- Real limitations: Licensing controversy in 2023 damaged trust (runtime fee was proposed then walked back — the risk of policy changes remains real); C# has a steeper initial curve than GDScript; heavier editor than Godot for simple projects
- Licensing reality: Unity Personal uses a USD 200K Total Finances ceiling over the trailing 12 months (with entity/client-specific definitions); this is not an install-count condition. Closed platforms have additional plan/platform requirements. Verify [current Unity terms](https://unity.com/legal/editor-terms-of-service/software) (checked 2026-09-21) before budgeting.
- Best fit: Mobile games; mid-scope 3D; games targeting console; developers with C# background; projects needing large asset store; teams of 2-5

**Unreal Engine 5**
- Genuine strengths: Best-in-class 3D visuals (Lumen, Nanite, Chaos physics); industry standard for AAA and photorealistic 3D; large open-world support is mature and production-tested; Blueprint visual scripting lowers C++ barrier; strong for games targeting high-end PC or console
- Real limitations: Steepest learning curve; heaviest editor (slow compile times, large project sizes); overkill for stylized/2D/small-scope games; C++ is genuinely hard; mobile requires device/rendering budgets and heavier workflows; not the default web route
- Licensing reality: Standard game/runtime royalty terms cover attributable lifetime gross revenue above USD 1M at 5%, with exemptions including Epic Games Store revenue; check the actual agreement. [Epic licensing](https://www.unrealengine.com/license) and [mobile support](https://dev.epicgames.com/documentation/en-us/unreal-engine/getting-started-with-mobile-development-in-unreal-engine), checked 2026-09-21.
- Best fit: AAA-quality 3D; large open-world games; photorealistic visuals; developers with C++ experience or willing to use Blueprint; games targeting high-end PC/console where visual fidelity is a core selling point

**Phaser 3**
- Browser-first 2D with scenes, loaders, input and optional Arcade/Matter physics; JavaScript or TypeScript. Good for small web games; 3D/native packaging and trusted backend scores are separate scope.
- Use the explicit 3.x pin. Phaser 4 is not a drop-in default. Currently MIT licensed; retain notices and check asset licenses.

**Three.js**
- Code-first 3D browser rendering with WebGL2. Application code owns gameplay, physics choices, DOM UI and lifecycle. Suitable for teams comfortable building those pieces; not a full editor-driven game engine.
- Currently MIT licensed. WebGPU and native/mobile packaging need separate acceptance, not an assumption from Chromium.

**libGDX**
- Code-first Java framework for teams comfortable owning application structure,
  screen flow and builds; Kotlin/KTX is an explicit separately verified choice.
- The included Java starter supports desktop compilation and real headless tests.
  Android/iOS/GWT are optional backend projects with separate toolchain acceptance.
  No built-in visual editor; assess authoring needs rather than promising parity
  with Unity/Godot editors. See [official libGDX](https://libgdx.com/) and the local
  version reference (checked 2026-09-21).

**Genre-specific guidance** (factor this into the recommendation):
- 2D → Godot for editor-led/native workflows; Phaser 3 for browser-first delivery
- 3D stylized / atmospheric / contained world → Godot viable, Unity solid alternative
- 3D open world (large, seamless) → Unity or Unreal; Godot is not production-proven for this
- 3D photorealistic / AAA-quality → Unreal
- Mobile-first → Unity strongly preferred
- Console-first → Unity or Unreal; Godot console support requires extra work
- Horror / narrative / walking sim → any engine; match to art style and team experience
- Action RPG / Soulslike → Unity or Unreal for 3D; community support and assets matter here
- Platformer 2D → Godot; Phaser 3 for browser-first scope
- Strategy / top-down / RTS → Godot or Unity depending on 2D vs 3D

**Recommendation format:**
1. Show a comparison table with the user's specific factors as rows
2. Give a primary recommendation with honest reasoning
3. Name the best alternative and when to choose it instead
4. Explicitly state: "This is a starting point, not a verdict — you can always migrate engines, and many developers switch between projects."
5. Use `AskUserQuestion` to confirm: "Does this recommendation feel right, or would you like to explore a different engine?"
   - Options: `[Primary engine] (Recommended)` / `[Alternative engine]` / `[Third engine]` / `Explore further` / `Type something`

**If the user picks "Explore further":**
Use `AskUserQuestion` with concept-specific deep-dive topics. Always generate these options from the user's actual concept — do not use generic options. Always include at minimum:
- The primary engine's specific limitations for this concept (e.g., "How far can Godot 3D actually go for [genre]?")
- The alternative engine's specific tradeoffs for this concept
- Language choice impact on this concept's technical challenges
- Any concept-specific technical concern (e.g., adaptive audio, open-world streaming, multiplayer netcode)

The user can select multiple topics. Answer each selected topic in depth before returning to the engine confirmation question.

---

## 3. Look Up Current Version

Once the engine is chosen:

- For `phaser` and `threejs`, installed project pins take precedence. For a new project offer the reference candidate Phaser `3.90.0` or Three.js `0.186.0` / `r186`, not a moving latest version. The staged scaffold pins are documented in `.claude/docs/web-game-development.md`; consult docs/codex-adapter/validation.md for observed runtime acceptance and limitations.
- An explicit Phaser 4 request requires an unsupported/migration discussion; do not write it into a Phaser 3 configuration. Three.js npm/revision and addon/type versions must agree. Keep exact direct dependency versions plus lockfile.

- For `libgdx`, retain installed project pins. The included Java candidate is
  1.14.2, Gradle 8.14.3, JDK 21, JUnit 5.13.4; using another version requires
  corresponding official reference/dependency validation. Record concrete build
  and runtime versions instead of calling any reference candidate "latest".

- If version was provided, use it
- For the original engine branches, if no version provided, use WebSearch to find the latest stable release:
  - Search: `"[engine] latest stable version [current year]"`
  - Confirm with the user: "The latest stable [engine] is [version]. Use this?"

---

## 4. Update CLAUDE.md Technology Stack

### Language Selection and Backends (libGDX)

Record Java or Kotlin explicitly. The shipped starter is Java (release 8 source
API target, built on JDK 21). Kotlin/KTX needs verified Kotlin plugin, KTX module
and version, JVM target, and selected backend compatibility; do not copy Java and
claim a Kotlin setup. Keep existing language choices until migration is accepted.
Select actual backends: `lwjgl3` desktop and `headless` test/server are separate.
Android/iOS/GWT require SDK/compiler/native/signing checks before support claims.
Core is shared code, not a runnable platform. Record Source Roots, Build JDK,
Gradle/wrapper checksum, Test Framework, Selected Backends and Build/Test Commands
in technical preferences. Use `core/src`, `lwjgl3/src`, `headless/src` plus only
actual selected modules; inspect custom sourceSets when adopting an existing game.


### Language Selection (web engines)

For Phaser 3/Three.js record JavaScript or TypeScript; TypeScript is the default scaffold language. An existing JavaScript project stays JavaScript unless migration is approved. The template is TypeScript; selecting JavaScript requires an explicit adaptation, not copying TS and claiming JS setup complete.

### Language Selection (Godot only)

If Godot was chosen, ask the user which language to use **before** showing the proposed Technology Stack:

> "Godot supports two primary languages:
>
>   **A) GDScript** — Python-like, Godot-native, fastest iteration. Best for beginners, solo devs, and teams coming from Python or Lua.
>   **B) C#** — .NET 8+, familiar to Unity developers, stronger IDE tooling (Rider / Visual Studio), slight performance advantage on heavy logic.
>   **C) Both** — GDScript for gameplay/UI scripting, C# for performance-critical systems. Advanced setup — requires .NET SDK alongside Godot.
>
> Which will this project primarily use?"

Record the choice. It determines the CLAUDE.md template, naming conventions, specialist routing, and which agent is spawned for code files throughout the project.

---

Read `CLAUDE.md` and show the user the proposed Technology Stack changes.
Ask: "May I write these engine settings to `CLAUDE.md`?"

Wait for confirmation before making any edits.

Update the Technology Stack section, replacing the `[CHOOSE]` placeholders with the actual values:

**For Godot** — use the template matching the language chosen above. See **Appendix A** at the bottom of this skill for all three variants (GDScript, C#, Both).

**For Unity:**
```markdown
- **Engine**: Unity [version]
- **Language**: C#
- **Build System**: Unity Build Pipeline
- **Asset Pipeline**: Unity Asset Import Pipeline + Addressables
```

**For Unreal:**
```markdown
- **Engine**: Unreal Engine [version]
- **Language**: C++ (primary), Blueprint (gameplay prototyping)
- **Build System**: Unreal Build Tool (UBT)
- **Asset Pipeline**: Unreal Content Pipeline
```

---

### Web Technology Stack

For `phaser`, write Engine as `Phaser 3 [version]`; for `threejs`, write
`Three.js [npm-version] ([revision])`. Write the selected Language, Build System
`Vite + TypeScript` (or the existing JS toolchain), and Asset Pipeline
`local assets + Vite; Phaser Loader` or `local assets + Vite; Three.js loaders`.
Use canonical `phaser`/`threejs` directory names for the reference import in Section 8.

### libGDX Technology Stack

Write Engine `libGDX [verified version]`, Language `[Java or verified Kotlin/KTX]`,
Build System `Gradle [actual version], JDK [actual build version], [selected modules]`,
and Asset Pipeline `assets/ classpath resources; AssetManager when adopted`.
Use `@docs/engine-reference/libgdx/VERSION.md` in Section 8. Java/Kotlin classes and
files use PascalCase, members/functions camelCase, constants UPPER_SNAKE_CASE;
retain the existing project's accepted conventions. Source target is independent
from the JDK running Gradle. Do not edit machine-wide JAVA_HOME/configuration.


## 5. Populate Technical Preferences

After updating CLAUDE.md, create or update `.claude/docs/technical-preferences.md` with
engine-appropriate defaults. Read the existing template first, then fill in:

### Engine & Language Section
- Fill from the engine choice made in step 4

### Naming Conventions (engine defaults)

**For Godot** — see **Appendix A** for GDScript, C#, and Both variants.

**For Unity (C#):**
- Classes: PascalCase (e.g., `PlayerController`)
- Public fields/properties: PascalCase (e.g., `MoveSpeed`)
- Private fields: _camelCase (e.g., `_moveSpeed`)
- Methods: PascalCase (e.g., `TakeDamage()`)
- Files: PascalCase matching class (e.g., `PlayerController.cs`)
- Constants: PascalCase or UPPER_SNAKE_CASE

**For Unreal (C++):**
- Classes: Prefixed PascalCase (`A` for Actor, `U` for UObject, `F` for struct)
- Variables: PascalCase (e.g., `MoveSpeed`)
- Functions: PascalCase (e.g., `TakeDamage()`)
- Booleans: `b` prefix (e.g., `bIsAlive`)
- Files: Match class without prefix (e.g., `PlayerController.h`)

**For Phaser 3 / Three.js (JavaScript or TypeScript):**
- Classes/types: PascalCase; variables/functions: camelCase; constants: UPPER_SNAKE_CASE.
- Files: PascalCase for scene/classes, camelCase for pure modules; preserve established project conventions.
- Events: named constants with documented payload types and an explicit unsubscribe owner.
- Rendering: Phaser renderer/Scale Manager choice or Three.js WebGL2; Physics: pure simulation unless an approved physics requirement exists.
- Testing: Vitest pure units and Playwright browser integration. Record existing scripts; do not add speculative libraries.

### Input & Platform Section

Populate `## Input & Platform` using the answers gathered in Section 2 (or extracted
from the game concept). Derive the values using this mapping:

| Platform target | Gamepad Support | Touch Support |
|-----------------|-----------------|---------------|
| PC only | Partial (recommended) | None |
| Console | Full | None |
| Mobile | None | Full |
| PC + Console | Full | None |
| PC + Mobile | Partial | Full |
| Web | Partial | Partial |

For **Primary Input**, use the dominant input for the game genre:
- Action/RPG/platformer targeting console → Gamepad
- Strategy/point-and-click/RTS → Keyboard/Mouse
- Mobile game → Touch
- Cross-platform → ask the user

Present the derived values and ask the user to confirm or adjust before writing.

Example filled section:
```markdown
## Input & Platform
- **Target Platforms**: PC, Console
- **Input Methods**: Keyboard/Mouse, Gamepad
- **Primary Input**: Gamepad
- **Gamepad Support**: Full
- **Touch Support**: None
- **Platform Notes**: All UI must support d-pad navigation. No hover-only interactions.
```

### Remaining Sections
- **Performance Budgets**: Use `AskUserQuestion`:
  - Prompt: "Should I set default performance budgets now, or leave them for later?"
  - Options: `[A] Set defaults now (60fps, 16.6ms frame budget, engine-appropriate draw call limit)` / `[B] Leave as [TO BE CONFIGURED] — I'll set these when I know my target hardware`
  - If [A]: populate with the suggested defaults. If [B]: leave as placeholder.
- **Testing**: Suggest engine-appropriate framework (GUT for Godot, NUnit for Unity, etc.) — ask before adding.
- **Forbidden Patterns**: Leave as placeholder — do NOT pre-populate.
- **Allowed Libraries**: Leave as placeholder — do NOT pre-populate dependencies the project does not currently need. Only add a library here when it is actively being integrated, not speculatively.

> **Guardrail**: Never add speculative dependencies to Allowed Libraries. For example, do NOT add GodotSteam unless Steam integration is actively beginning in this session. Post-launch integrations should be added to Allowed Libraries when that work begins, not during engine setup.

### Engine Specialists Routing

Also populate the `## Engine Specialists` section in `technical-preferences.md` with the correct routing for the chosen engine:

**For Godot** — see **Appendix A** for the routing table matching the language chosen.

**For Unity:**
```markdown
## Engine Specialists
- **Primary**: unity-specialist
- **Language/Code Specialist**: unity-specialist (C# review — primary covers it)
- **Shader Specialist**: unity-shader-specialist (Shader Graph, HLSL, URP/HDRP materials)
- **UI Specialist**: unity-ui-specialist (UI Toolkit UXML/USS, UGUI Canvas, runtime UI)
- **Additional Specialists**: unity-dots-specialist (ECS, Jobs system, Burst compiler), unity-addressables-specialist (asset loading, memory management, content catalogs)
- **Routing Notes**: Invoke primary for architecture and general C# code review. Invoke DOTS specialist for any ECS/Jobs/Burst code. Invoke shader specialist for rendering and visual effects. Invoke UI specialist for all interface implementation. Invoke Addressables specialist for asset management systems.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (.cs files) | unity-specialist |
| Shader / material files (.shader, .shadergraph, .mat) | unity-shader-specialist |
| UI / screen files (.uxml, .uss, Canvas prefabs) | unity-ui-specialist |
| Scene / prefab / level files (.unity, .prefab) | unity-specialist |
| Native extension / plugin files (.dll, native plugins) | unity-specialist |
| General architecture review | unity-specialist |
```

**For Unreal:**
```markdown
## Engine Specialists
- **Primary**: unreal-specialist
- **Language/Code Specialist**: ue-blueprint-specialist (Blueprint graphs) or unreal-specialist (C++)
- **Shader Specialist**: unreal-specialist (no dedicated shader specialist — primary covers materials)
- **UI Specialist**: ue-umg-specialist (UMG widgets, CommonUI, input routing, widget styling)
- **Additional Specialists**: ue-gas-specialist (Gameplay Ability System, attributes, gameplay effects), ue-replication-specialist (property replication, RPCs, client prediction, netcode)
- **Routing Notes**: Invoke primary for C++ architecture and broad engine decisions. Invoke Blueprint specialist for Blueprint graph architecture and BP/C++ boundary design. Invoke GAS specialist for all ability and attribute code. Invoke replication specialist for any multiplayer or networked systems. Invoke UMG specialist for all UI implementation.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (.cpp, .h files) | unreal-specialist |
| Shader / material files (.usf, .ush, Material assets) | unreal-specialist |
| UI / screen files (.umg, UMG Widget Blueprints) | ue-umg-specialist |
| Scene / prefab / level files (.umap, .uasset) | unreal-specialist |
| Native extension / plugin files (Plugin .uplugin, modules) | unreal-specialist |
| Blueprint graphs (.uasset BP classes) | ue-blueprint-specialist |
| General architecture review | unreal-specialist |
```

### phaser routing
```markdown
## Engine Specialists
- **Primary**: phaser-specialist
- **Language/Code Specialist**: phaser-specialist
- **Shader Specialist**: technical-artist
- **UI Specialist**: phaser-specialist
- **Additional Specialists**: None — reuse existing domain owners
- **Routing Notes**: Phaser UI lifecycle is reviewed by phaser-specialist; DOM HUD/HTML/CSS/focus/accessibility implementation and review goes to ui-programmer. Consult technical-artist with phaser-specialist for shader/renderer changes. Programmer owners still implement features.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|---|---|
| Game code (.js, .ts, .mjs) | phaser-specialist |
| Shader (.glsl, .vert, .frag) | technical-artist |
| Phaser Scene / canvas UI lifecycle | phaser-specialist |
| DOM UI (.html, .css, UI .ts/.js) | ui-programmer |
| General architecture review | phaser-specialist |
```

### threejs routing
```markdown
## Engine Specialists
- **Primary**: threejs-specialist
- **Language/Code Specialist**: threejs-specialist
- **Shader Specialist**: technical-artist
- **UI Specialist**: ui-programmer
- **Additional Specialists**: None — reuse existing domain owners
- **Routing Notes**: Consult threejs-specialist for scene graph, loaders, camera, renderer and resource ownership; technical-artist for GLSL/materials; ui-programmer for DOM UI/focus/accessibility. Programmer owners still implement features; suffix alone does not determine UI ownership.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|---|---|
| Game code (.js, .ts, .mjs) | threejs-specialist |
| Shader (.glsl, .vert, .frag) | technical-artist |
| Scene / renderer / loader modules | threejs-specialist |
| DOM UI (.html, .css, UI .ts/.js) | ui-programmer |
| General architecture review | threejs-specialist |
```

### libgdx routing
```markdown
## Engine Specialists
- **Primary**: libgdx-specialist
- **Language/Code Specialist**: libgdx-specialist
- **Shader Specialist**: libgdx-graphics-specialist
- **UI Specialist**: libgdx-scene2d-specialist
- **Additional Specialists**: libgdx-ashley-specialist, libgdx-core-specialist
- **Routing Notes**: Inspect subsystem imports and module/path context; ambiguous Java/Kotlin goes to the lead. Ashley/Box2D are optional. Lead delegates real subs; existing programmer owners implement features and full/lean/solo gates stay selected.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|---|---|
| Ambiguous game code (.java, .kt) / architecture | libgdx-specialist |
| Stage / Table / Skin / UI screen input and layout | libgdx-scene2d-specialist |
| SpriteBatch / ModelBatch / shader (.glsl, .vert, .frag) / FBO | libgdx-graphics-specialist |
| Ashley components / systems / Box2D contacts and stepping | libgdx-ashley-specialist |
| Lifecycle / AssetManager / files / input / audio / net | libgdx-core-specialist |
| Gradle (.gradle, .gradle.kts) / wrapper / backend modules | libgdx-core-specialist |
```


### Collaborative Step
Present the filled-in preferences to the user. For Godot, include the chosen language and note where the full naming conventions and routing tables live:
> "Here are the default technical preferences for [engine] ([language if Godot]). The naming conventions and specialist routing are in Appendix A of this skill — I'll apply the [GDScript/C#/Both] variant. Want to customize any of these, or shall I save the defaults?"

For all other engines, present the defaults directly without referencing the appendix.

Wait for approval before writing the file.

---

## 6. Determine Knowledge Gap

For web engines and libGDX, always read the version-specific references and installed package
metadata. Do not apply the historical model cutoff below as API verification.
Retain the full curated web reference set even for a known version; update it only
with checked source evidence. If a role cannot browse, route uncertainty to this
workflow/coordinator rather than granting that role WebSearch implicitly.

For the original engines, check whether the engine version is likely beyond the LLM's training data.

**Known approximate coverage** (update this as models change):
- LLM knowledge cutoff: **May 2025**
- Godot: training data likely covers up to ~4.3
- Unity: training data likely covers up to ~2023.x / early 6000.x
- Unreal: training data likely covers up to ~5.3 / early 5.4

Compare the user's chosen version against these baselines:

- **Within training data** → `LOW RISK` — reference docs optional but recommended
- **Near the edge** → `MEDIUM RISK` — reference docs recommended
- **Beyond training data** → `HIGH RISK` — reference docs required

Inform the user which category they're in and why.

---

## 7. Populate Engine Reference Docs

### If WITHIN training data (LOW RISK):

Create a minimal `docs/engine-reference/<engine>/VERSION.md`:

```markdown
# [Engine] — Version Reference

| Field | Value |
|-------|-------|
| **Engine Version** | [version] |
| **Project Pinned** | [today's date] |
| **LLM Knowledge Cutoff** | May 2025 |
| **Risk Level** | LOW — version is within LLM training data |

## Note

This engine version is within the LLM's training data. Engine reference
docs are optional but can be added later if agents suggest incorrect APIs.

Run `/setup-engine refresh` to populate full reference docs at any time.
```

Do NOT create breaking-changes.md, deprecated-apis.md, etc. — they would
add context cost with minimal value.

### If BEYOND training data (MEDIUM or HIGH RISK):

Create the full reference doc set by searching the web:

1. **Search for the official migration/upgrade guide**:
   - `"[engine] [old version] to [new version] migration guide"`
   - `"[engine] [version] breaking changes"`
   - `"[engine] [version] changelog"`
   - `"[engine] [version] deprecated API"`

2. **Fetch and extract** from official documentation:
   - Breaking changes between each version from the training cutoff to current
   - Deprecated APIs with replacements
   - New features and best practices

Ask: "May I create the engine reference docs under `docs/engine-reference/<engine>/`?"

Wait for confirmation before writing any files.

3. **Create the full reference directory**:
   ```
   docs/engine-reference/<engine>/
   ├── VERSION.md              # Version pin + knowledge gap analysis
   ├── breaking-changes.md     # Version-by-version breaking changes
   ├── deprecated-apis.md      # "Don't use X → Use Y" tables
   ├── current-best-practices.md  # New practices since training cutoff
   └── modules/                # Per-subsystem references (create as needed)
   ```

4. **Populate each file** using real data from the web searches, following
   the format established in existing reference docs. Every file must have
   a "Last verified: [date]" header.

5. **For module files**: Only create modules for subsystems where significant
   changes occurred. Don't create empty or minimal module files.

---

## 8. Update CLAUDE.md Import

Ask: "May I update the `@` import in `CLAUDE.md` to point to the new engine reference?"

Wait for confirmation, then update the `@` import under "Engine Version Reference" to point to the
correct engine:

```markdown
## Engine Version Reference

@docs/engine-reference/<engine>/VERSION.md
```

If the previous import pointed to a different engine (e.g., switching from
Godot to Unity), update it.

---

## 9. Update Agent Instructions

Ask: "May I add a Version Awareness section to the engine specialist agent files?" before making any edits.

For the chosen engine's specialist agents, verify they have a
"Version Awareness" section. If not, add one following the pattern in
the existing Godot specialist agents.

The section should instruct the agent to:
1. Read `docs/engine-reference/<engine>/VERSION.md`
2. Check deprecated APIs before suggesting code
3. Check breaking changes for relevant version transitions
4. Verify uncertain APIs with WebSearch only when the role allowlist permits it; otherwise request source verification from the coordinator or this setup workflow

---

## 10. Refresh Subcommand

If invoked as `/setup-engine refresh`:

1. Read the existing `docs/engine-reference/<engine>/VERSION.md` to get
   the current engine and version
2. Use WebSearch to check for:
   - New engine releases since last verification
   - Updated migration guides
   - Newly deprecated APIs
3. Update all reference docs with new findings
4. Update "Last verified" dates on all modified files
5. Report what changed

---

## 11. Upgrade Subcommand

If invoked as `/setup-engine upgrade [old-version] [new-version]`:

### Step 1 — Read Current Version State

Read `docs/engine-reference/<engine>/VERSION.md` to confirm the current pinned
version, risk level, and any migration note URLs already recorded. If
`old-version` was not provided as an argument, use the pinned version from this
file.

### Step 2 — Fetch Migration Guide

Use WebSearch and WebFetch to locate the official migration guide between
`old-version` and `new-version`:

- Search: `"[engine] [old-version] to [new-version] migration guide"`
- Search: `"[engine] [new-version] breaking changes changelog"`
- Fetch the migration guide URL from VERSION.md if one is already recorded,
  or use the URL found via search.

Extract: renamed APIs, removed APIs, changed defaults, behavior changes, and
any "must migrate" items.

### Step 3 — Pre-Upgrade Audit

Scan `src/` and the actual configured module source roots (including Java/Kotlin `core/src` and selected backends) for code that uses APIs known to be deprecated or changed in the
target version:

- Use Grep to search for deprecated API names extracted from the migration
  guide (e.g., old function names, removed node types, changed property names)
- List each file that matches, with the specific API reference found

Present the audit results as a table:

```
Pre-Upgrade Audit: [engine] [old-version] → [new-version]
==========================================================

Files requiring changes:
  File                              | Deprecated API Found       | Effort
  --------------------------------- | -------------------------- | ------
  src/gameplay/player_movement.gd   | old_api_name               | Low
  src/ui/hud.gd                     | removed_node_type          | Medium

Breaking changes to watch for:
  - [change description from migration guide]
  - [change description from migration guide]

Recommended migration order (dependency-sorted):
  1. [system/layer with fewest dependencies first]
  2. [next system]
  ...
```

If no deprecated APIs are found in `src/`, report: "No deprecated API usage
found in src/ — upgrade may be low-risk."

### Step 4 — Confirm Before Updating

Ask the user before making any changes:

> "Pre-upgrade audit complete. Found [N] files using deprecated APIs.
> Proceed with upgrading VERSION.md to [new-version]?
> (This will update the pinned version and add migration notes — it does NOT
> change any source files. Source migration is done manually or via stories.)"

Wait for explicit confirmation before continuing.

### Step 5 — Update VERSION.md

After confirmation:

1. Update `docs/engine-reference/<engine>/VERSION.md`:
   - `Engine Version` → `[new-version]`
   - `Project Pinned` → today's date
   - `Last Docs Verified` → today's date
   - Re-evaluate and update the `Risk Level` and `Post-Cutoff Version Timeline`
     table if the new version falls beyond the LLM knowledge cutoff
   - Add a `## Migration Notes — [old-version] → [new-version]` section
     containing: migration guide URL, key breaking changes, deprecated APIs
     found in this project, and recommended migration order from the audit

2. If `breaking-changes.md` or `deprecated-apis.md` exist in the engine
   reference directory, append the new version's changes to those files.

### Step 6 — Post-Upgrade Reminder

After updating VERSION.md, output:

```
VERSION.md updated: [engine] [old-version] → [new-version]

Next steps:
1. Migrate deprecated API usages in the [N] files listed above
2. Run /setup-engine refresh after upgrading the actual engine binary to
   verify no new deprecations were missed
3. Run /architecture-review — the engine upgrade may invalidate ADRs that
   reference specific APIs or engine capabilities
4. If any ADRs are invalidated, run /propagate-design-change to update
   downstream stories
```

---

## Web Scaffold Handoff (after configuration)

Read `.claude/docs/web-game-development.md`. Use the included
`templates/web/phaser/` and `templates/web/threejs/` sources and the CLI interface
`python3 tools/ccgs_codex.py scaffold-web ENGINE --target PATH [--write]`.
Record each copy/install/typecheck/unit/build/browser result separately;
consult `docs/codex-adapter/validation.md` for the release evidence.

Delegate copy/build to an authorized `tools-programmer` (this
skill has no Bash permission). Pass the canonical engine, exact target path,
selected language, pins and user's existing authorization. Default preview is
read-only; `--write` copies only its declared manifest and never overwrites files,
installs packages or changes engine configuration. Existing studio files may
coexist; collisions, symlinks and traversal are blocking. Do not bypass a refusal.
For an existing game, merge only approved missing pieces instead of copying over it.
Dependency installation and test execution are separate explicit work; capture
actual npm/typecheck/unit/build/browser results. Configuration completion is not
runtime acceptance.

## libGDX Scaffold Handoff (after configuration)

Read `.claude/docs/libgdx-development.md`. Delegate preview/copy/build to an
authorized `tools-programmer` or `libgdx-core-specialist`; setup-engine itself has
no Bash permission. Interface: `python3 tools/ccgs_codex.py scaffold-libgdx --target PATH [--write]`.
Default preview returns the exact manifest, binary hashes and modes. `--write`
never overwrites, follows symlinks, installs dependencies or configures the engine.
Inspect collisions and merge only accepted missing pieces for an existing game.
The Java starter is core/lwjgl3/headless; execute its exact pinned wrapper under
the verified JDK, preserving dependency locks. Capture pure tests, actual backend
lifecycle and desktop distribution results separately. Missing JDK/network/native
support is a blocker for that evidence layer, not a reason to fabricate success.
On Windows use gradlew.bat; macOS desktop needs first-thread setup documented by
the starter. Optional Kotlin/backends are NOT RUN until separately validated.


## 12. Output Summary

After setup is complete, output:

```
Engine Setup Complete
=====================
Engine:          [name] [version]
Language:        [GDScript | C# | GDScript + C# | C++ + Blueprint | TypeScript | JavaScript | Java | Kotlin/KTX]
Knowledge Risk:  [LOW/MEDIUM/HIGH]
Reference Docs:  [created/skipped]
CLAUDE.md:       [updated]
Tech Prefs:      [created/updated]
Agent Config:    [verified]
Web Runtime:     [N/A / NOT RUN / exact observed results]
libGDX Runtime:  [N/A / pure tests / actual headless / desktop build / GPU playtest separately]
Backends/Tools:  [actual selected platforms, language, JDK and Gradle versions; optional gaps]

Next Steps:
1. Review docs/engine-reference/<engine>/VERSION.md
2. [If from /brainstorm] Run /map-systems to decompose your concept into individual systems
3. [If from /brainstorm] Run /design-system to author per-system GDDs (guided, section-by-section)
4. [If from /brainstorm] Run /prototype [core-mechanic] to validate the core idea before writing GDDs
5. [If fresh start] Run /brainstorm to discover your game concept
6. Create your first milestone: /sprint-plan new
```

---

Verdict: **COMPLETE** — engine configured and reference docs populated.

## Guardrails

- NEVER guess an engine version — always verify via WebSearch or user confirmation
- NEVER overwrite existing reference docs without asking — append or update
- If reference docs already exist for a different engine, ask before replacing
- Always show the user what you're about to change before making CLAUDE.md edits
- If WebSearch returns ambiguous results, show the user and let them decide
- When the user chose **GDScript**: copy the GDScript CLAUDE.md template from Appendix A1 exactly. NEVER add "C++ via GDExtension" to the Language field. GDScript projects may use GDExtension, but it is not a primary project language. The `godot-gdextension-specialist` in the routing table is available for when native extensions are needed — it does not make C++ a project language.

---

## Appendix A — Godot Language Configuration

All Godot-specific variants for language-dependent configuration. Referenced from Sections 4 and 5 — only relevant when Godot is the chosen engine. Use the subsection matching the language chosen in Section 4.

---

### A1. CLAUDE.md Technology Stack Templates

**GDScript:**
```markdown
- **Engine**: Godot [version]
- **Language**: GDScript
- **Build System**: SCons (engine), Godot Export Templates
- **Asset Pipeline**: Godot Import System + custom resource pipeline
```

> **Guardrail**: When using this GDScript template, write the Language field as exactly "`GDScript`" — no additions. Do NOT append "C++ via GDExtension" or any other language. The C# template below includes GDExtension because C# projects commonly wrap native code; GDScript projects do not.

**C#:**
```markdown
- **Engine**: Godot [version]
- **Language**: C# (.NET 8+, primary), C++ via GDExtension (native plugins only)
- **Build System**: .NET SDK + Godot Export Templates
- **Asset Pipeline**: Godot Import System + custom resource pipeline
```

**Both — GDScript + C#:**
```markdown
- **Engine**: Godot [version]
- **Language**: GDScript (gameplay/UI scripting), C# (performance-critical systems), C++ via GDExtension (native only)
- **Build System**: .NET SDK + Godot Export Templates
- **Asset Pipeline**: Godot Import System + custom resource pipeline
```

---

### A2. Naming Conventions

**GDScript:**
- Classes: PascalCase (e.g., `PlayerController`)
- Variables/functions: snake_case (e.g., `move_speed`)
- Signals: snake_case past tense (e.g., `health_changed`)
- Files: snake_case matching class (e.g., `player_controller.gd`)
- Scenes: PascalCase matching root node (e.g., `PlayerController.tscn`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_HEALTH`)

**C#:**
- Classes: PascalCase (`PlayerController`) — must also be `partial`
- Public properties/fields: PascalCase (`MoveSpeed`, `JumpVelocity`)
- Private fields: `_camelCase` (`_currentHealth`, `_isGrounded`)
- Methods: PascalCase (`TakeDamage()`, `GetCurrentHealth()`)
- Signal delegates: PascalCase + `EventHandler` suffix (`HealthChangedEventHandler`)
- Files: PascalCase matching class (`PlayerController.cs`)
- Scenes: PascalCase matching root node (`PlayerController.tscn`)
- Constants: PascalCase (`MaxHealth`, `DefaultMoveSpeed`)

**Both — GDScript + C#:**
Use GDScript conventions for `.gd` files and C# conventions for `.cs` files. Mixed-language files do not exist — the boundary is per-file. When in doubt about which language a new system should use, ask the user and record the decision in `technical-preferences.md`.

---

### A3. Engine Specialists Routing

**GDScript:**
```markdown
## Engine Specialists
- **Primary**: godot-specialist
- **Language/Code Specialist**: godot-gdscript-specialist (all .gd files)
- **Shader Specialist**: godot-shader-specialist (.gdshader files, VisualShader resources)
- **UI Specialist**: godot-specialist (no dedicated UI specialist — primary covers all UI)
- **Additional Specialists**: godot-gdextension-specialist (GDExtension / native C++ bindings only)
- **Routing Notes**: Invoke primary for architecture decisions, ADR validation, and cross-cutting code review. Invoke GDScript specialist for code quality, signal architecture, static typing enforcement, and GDScript idioms. Invoke shader specialist for material design and shader code. Invoke GDExtension specialist only when native extensions are involved.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (.gd files) | godot-gdscript-specialist |
| Shader / material files (.gdshader, VisualShader) | godot-shader-specialist |
| UI / screen files (Control nodes, CanvasLayer) | godot-specialist |
| Scene / prefab / level files (.tscn, .tres) | godot-specialist |
| Native extension / plugin files (.gdextension, C++) | godot-gdextension-specialist |
| General architecture review | godot-specialist |
```

**C#:**
```markdown
## Engine Specialists
- **Primary**: godot-specialist
- **Language/Code Specialist**: godot-csharp-specialist (all .cs files)
- **Shader Specialist**: godot-shader-specialist (.gdshader files, VisualShader resources)
- **UI Specialist**: godot-specialist (no dedicated UI specialist — primary covers all UI)
- **Additional Specialists**: godot-gdextension-specialist (GDExtension / native C++ bindings only)
- **Routing Notes**: Invoke primary for architecture decisions, ADR validation, and cross-cutting code review. Invoke C# specialist for code quality, [Signal] delegate patterns, [Export] attributes, .csproj management, and C#-specific Godot idioms. Invoke shader specialist for material design and shader code. Invoke GDExtension specialist only when native C++ plugins are involved.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (.cs files) | godot-csharp-specialist |
| Shader / material files (.gdshader, VisualShader) | godot-shader-specialist |
| UI / screen files (Control nodes, CanvasLayer) | godot-specialist |
| Scene / prefab / level files (.tscn, .tres) | godot-specialist |
| Project config (.csproj, NuGet) | godot-csharp-specialist |
| Native extension / plugin files (.gdextension, C++) | godot-gdextension-specialist |
| General architecture review | godot-specialist |
```

**Both — GDScript + C#:**
```markdown
## Engine Specialists
- **Primary**: godot-specialist
- **GDScript Specialist**: godot-gdscript-specialist (.gd files — gameplay/UI scripts)
- **C# Specialist**: godot-csharp-specialist (.cs files — performance-critical systems)
- **Shader Specialist**: godot-shader-specialist (.gdshader files, VisualShader resources)
- **UI Specialist**: godot-specialist (no dedicated UI specialist — primary covers all UI)
- **Additional Specialists**: godot-gdextension-specialist (GDExtension / native C++ bindings only)
- **Routing Notes**: Invoke primary for cross-language architecture decisions and which systems belong in which language. Invoke GDScript specialist for .gd files. Invoke C# specialist for .cs files and .csproj management. Prefer signals over direct cross-language method calls at the boundary.

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (.gd files) | godot-gdscript-specialist |
| Game code (.cs files) | godot-csharp-specialist |
| Cross-language boundary decisions | godot-specialist |
| Shader / material files (.gdshader, VisualShader) | godot-shader-specialist |
| UI / screen files (Control nodes, CanvasLayer) | godot-specialist |
| Scene / prefab / level files (.tscn, .tres) | godot-specialist |
| Project config (.csproj, NuGet) | godot-csharp-specialist |
| Native extension / plugin files (.gdextension, C++) | godot-gdextension-specialist |
| General architecture review | godot-specialist |
```

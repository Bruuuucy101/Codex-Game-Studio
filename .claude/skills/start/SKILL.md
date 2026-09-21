---
name: start
description: "First-time onboarding — asks where you are, then guides you to the right workflow. No assumptions."
argument-hint: "[no arguments]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Write, AskUserQuestion
model: sonnet
---

# Guided Onboarding

This skill writes authorized initial stage/kind and review-mode configuration.
Tool contract/configuration authoring belongs to `/setup-tool`; no implementation
is implied by onboarding. Honor decisions and write authorization already supplied.

This skill is the entry point for new users. It does NOT assume you have a game idea, an engine preference, or any prior experience. It asks first, then routes you to the right workflow.

---

## Phase 1: Detect Project State

Before asking anything, silently gather context so you can tailor your guidance. Do NOT show these results unprompted — they inform your recommendations, not the conversation opener.

First run `python3 tools/ccgs_codex.py project-kind` (read-only), and read
`.claude/docs/tooling-projects.md` if tooling is requested or a contract exists.
Use this shared result, not script counts. `conflict` requires repairing invalid
configuration before dependent writes. Surface contradictions without resetting
state. Valid explicit kind/stage remains authoritative. A meaningful contract
alongside game evidence is a game component. Bundled tools/tests/templates/examples
are not completed projects. If the user already specified a standalone tool, use
E directly; do not ask the game-idea question again. Returning standalone users
resume through `/setup-tool update` and `/project-stage-detect` with saved state.

For game/unknown routes, also check:
- **Engine configured?** Read `.claude/docs/technical-preferences.md`. If the Engine field contains `[TO BE CONFIGURED]`, the engine is not set.
- **Game concept exists?** Check for `design/gdd/game-concept.md`.
- **Source code exists?** Inspect actual `src/` plus conventional module roots `core/src`, `lwjgl3/src`, `headless/src`, `desktop/src`, `android/src`, `ios/src`, `html/src`, including `.java` and `.kt` as well as `.gd`, `.cs`, `.cpp`, `.h`, `.rs`, `.py`, `.js`, `.ts`, `.mjs`. The read-only `source-files` diagnostic lists these; custom Gradle sourceSets need explicit inspection. Exclude templates/examples, test roots, vendor, generated/build and dependency directories. Bundled Java templates never mean a game is already configured.
- **Prototypes exist?** Check for subdirectories in `prototypes/`.
- **Design docs exist?** Count markdown files in `design/gdd/`.
- **Production artifacts?** Check for files in `production/sprints/` or `production/milestones/`.

Store these findings internally to validate the user's self-assessment and tailor recommendations.

---

## Phase 2: Ask Where the User Is

This is the first thing the user sees. Use `AskUserQuestion` with these exact options so the user can click rather than type:

- **Prompt**: "Welcome to Claude Code Game Studios! Before I suggest anything, I'd like to understand where you're starting from. Where are you at with your game idea or development tool right now?"
- **Options**:
  - `A) No idea yet` — I don't have a game concept at all. I want to explore and figure out what to make.
  - `B) Vague idea` — I have a rough theme, feeling, or genre in mind (e.g., "something with space" or "a cozy farming game") but nothing concrete.
  - `C) Clear concept` — I know the core idea — genre, basic mechanics, maybe a pitch sentence — but haven't formalized it into documents yet.
  - `D) Existing work` — I already have design docs, prototypes, code, or significant planning done. I want to organize or continue the work.
  - `E) Game-development tool` — I want to build or adopt a standalone converter, validator or pipeline, or add one to a game.

Wait for a selection unless the user's request already specifies it. Supplied
requirements/authorization are decisions, not a reason to repeat onboarding.

---

## Phase 3: Route Based on Answer

#### If A: No idea yet

The user needs creative exploration before anything else.

1. Acknowledge that starting from zero is completely fine
2. Briefly explain what `/brainstorm` does (guided ideation using professional frameworks — MDA, player psychology, verb-first design). Mention that it has two modes: `/brainstorm open` for fully open exploration, or `/brainstorm [hint]` if they have even a vague theme (e.g., "space", "cozy", "horror").
3. Recommend running `/brainstorm open` as the next step, but invite them to use a hint if something comes to mind
4. Show the recommended path:
   **Concept phase:**
   - `/brainstorm open` — discover your game concept
   - `/setup-engine` — configure the engine (brainstorm will recommend one)
   - `/prototype` — throwaway concept build: validate the core idea is fun before designing (1–3 days)
   - `/art-bible` — define visual identity (uses the Visual Identity Anchor brainstorm produces)
   - `/map-systems` — decompose the concept into systems
   - `/design-system` — author a GDD for each MVP system
   - `/review-all-gdds` — cross-system consistency check
   - `/gate-check` — validate readiness before architecture work
   **Architecture phase:**
   - `/create-architecture` — produce the master architecture blueprint and Required ADR list
   - `/architecture-decision (×N)` — record key technical decisions, following the Required ADR list
   - `/create-control-manifest` — compile decisions into an actionable rules sheet
   - `/architecture-review` — validate architecture coverage
   **Pre-Production phase:**
   - `/ux-design` — author UX specs for key screens (main menu, HUD, core interactions)
   - `/vertical-slice` — production-quality end-to-end build to validate the full game loop
   - `/playtest-report (×1+)` — document each vertical slice playtest session
   - `/create-epics` — map systems to epics
   - `/create-stories` — break epics into implementable stories
   - `/sprint-plan` — plan the first sprint
   **Production phase:** → pick up stories with `/dev-story`

#### If B: Vague idea

1. Ask them to share their vague idea — even a few words is enough
2. Validate the idea as a starting point (don't judge or redirect)
3. Recommend running `/brainstorm [their hint]` to develop it
4. Show the recommended path:
   **Concept phase:**
   - `/brainstorm [hint]` — develop the idea into a full concept
   - `/setup-engine` — configure the engine
   - `/prototype` — throwaway concept build: validate the core idea is fun before designing (1–3 days)
   - `/art-bible` — define visual identity (uses the Visual Identity Anchor brainstorm produces)
   - `/map-systems` — decompose the concept into systems
   - `/design-system` — author a GDD for each MVP system
   - `/review-all-gdds` — cross-system consistency check
   - `/gate-check` — validate readiness before architecture work
   **Architecture phase:**
   - `/create-architecture` — produce the master architecture blueprint and Required ADR list
   - `/architecture-decision (×N)` — record key technical decisions, following the Required ADR list
   - `/create-control-manifest` — compile decisions into an actionable rules sheet
   - `/architecture-review` — validate architecture coverage
   **Pre-Production phase:**
   - `/ux-design` — author UX specs for key screens (main menu, HUD, core interactions)
   - `/vertical-slice` — production-quality end-to-end build to validate the full game loop
   - `/playtest-report (×1+)` — document each vertical slice playtest session
   - `/create-epics` — map systems to epics
   - `/create-stories` — break epics into implementable stories
   - `/sprint-plan` — plan the first sprint
   **Production phase:** → pick up stories with `/dev-story`

#### If C: Clear concept

1. Ask them to describe their concept in one sentence — genre and core mechanic. Use plain text, not AskUserQuestion (it's an open response).
2. Acknowledge the concept, then use `AskUserQuestion` to offer two paths:
   - **Prompt**: "How would you like to proceed?"
   - **Options**:
     - `Formalize it first` — Run `/brainstorm [concept]` to structure it into a proper game concept document
     - `Jump straight in` — Go to `/setup-engine` now and write the GDD manually afterward
3. Show the recommended path:
   **Concept phase:**
   - `/brainstorm` or `/setup-engine` — (their pick from step 2)
   - `/prototype` — throwaway concept build: validate the core idea is fun before designing (1–3 days)
   - `/art-bible` — define visual identity (after brainstorm if run, or after concept doc exists)
   - `/design-review` — validate the concept doc
   - `/map-systems` — decompose the concept into individual systems
   - `/design-system` — author a GDD for each MVP system
   - `/review-all-gdds` — cross-system consistency check
   - `/gate-check` — validate readiness before architecture work
   **Architecture phase:**
   - `/create-architecture` — produce the master architecture blueprint and Required ADR list
   - `/architecture-decision (×N)` — record key technical decisions, following the Required ADR list
   - `/create-control-manifest` — compile decisions into an actionable rules sheet
   - `/architecture-review` — validate architecture coverage
   **Pre-Production phase:**
   - `/ux-design` — author UX specs for key screens (main menu, HUD, core interactions)
   - `/vertical-slice` — production-quality end-to-end build to validate the full game loop
   - `/playtest-report (×1+)` — document each vertical slice playtest session
   - `/create-epics` — map systems to epics
   - `/create-stories` — break epics into implementable stories
   - `/sprint-plan` — plan the first sprint
   **Production phase:** → pick up stories with `/dev-story`

#### If D: Existing work

1. Share what you found in Phase 1:
   - "I can see you have [X source files / Y design docs / Z prototypes]..."
   - "Your engine is [configured as X / not yet configured]..."

2. **Sub-case D1 — Early stage** (engine not configured or only a game concept exists):
   - Recommend `/setup-engine` first if engine not configured
   - Then `/project-stage-detect` for a gap inventory

   **Sub-case D2 — GDDs, ADRs, or stories already exist:**
   - Explain: "Having files isn't the same as the template's skills being able to use them. GDDs might be missing required sections. `/adopt` checks this specifically."
   - Recommend:
     1. `/project-stage-detect` — understand what phase and what's missing entirely
     2. `/adopt` — audit whether existing artifacts are in the right internal format

3. Show the recommended path for D2:
   - `/project-stage-detect` — phase detection + existence gaps
   - `/adopt` — format compliance audit + migration plan
   - `/setup-engine` — if engine not configured
   - `/design-system retrofit [path]` — fill missing GDD sections
   - `/architecture-decision retrofit [path]` — add missing ADR sections
   - `/architecture-review` — bootstrap the TR requirement registry
   - `/gate-check` — validate readiness for next phase

---

#### If E: Game-development tool

1. Use supplied name, purpose and standalone/component intent; otherwise ask only
   for these missing facts. Read existing state and `tools/TOOL_SPEC.md` if present.
2. Route to `/setup-tool [name/description]` (author/update/adopt as appropriate).
   It writes the recognized contract, never `docs/project-spec.md` as a substitute.
3. Explain lead-programmer → game-pipeline-developer implementation and independent
   lead/pipeline/QA review. Engine-agnostic work needs no game engine setup.
4. Apply the explicit state mapping below only for a confirmed standalone choice.
   A game component preserves the game's configuration/stage and review mode.

---

## Phase 3b: Write Initial Stage File

After confirming the starting path (and before resolving review mode), write an
initial stage only if absent or an explicitly authorized reset/reclassification
requires it. Preserve an existing valid stage (especially Production/Polish/Release)
on resume and for mixed-game tooling. Never downgrade it from file-count heuristics.
If kind/stage conflict, resolve the concrete scope before writing. Create the
`production/` directory if needed.

Stage mapping:
- **Path E, confirmed standalone tool**: write `tooling` to `production/project-kind.txt` and `Tooling Project` to `production/stage.txt`, each with one LF; `/setup-tool` owns contract/configuration authoring
- **Path E, game component**: do not change marker or stage; preserve game stack/imports and review mode
- **Path A, B, or C (starting from scratch)**: write `Concept`
- **Path D, existing project, engine not configured or only a game concept exists**: write `Concept`
- **Path D, existing project with GDDs but no architecture documents**: write `Systems Design`
- **Path D, existing project with full architecture (ADRs, architecture doc)**: write `Technical Setup`

These scoped state writes follow the confirmed path or existing authorization; do
not treat a candidate classification as consent. Report the files actually written.

If written, say: "I've set `production/stage.txt` to `[stage]`." Otherwise report
the existing stage as preserved; never claim a state write that did not occur.

---

## Phase 3c: Set Review Mode

Check if `production/review-mode.txt` already exists.

**If it exists**: Read it and show the current mode — "Review mode is set to `[current]`." — then proceed to Phase 4. Do not ask again.

**If it does not exist**: use a mode explicitly supplied by the user; otherwise use `AskUserQuestion`:

- **Prompt**: "One setup choice: how much design review would you want as you work through the workflow?"
- **Options**:
  - `Full` — Director specialists review at each key workflow step. Best for teams, learning the workflow, or when you want thorough feedback on every decision.
  - `Lean (recommended)` — Directors only at phase gate transitions (/gate-check). Skips per-skill reviews. Balanced approach for solo devs and small teams.
  - `Solo` — No director reviews at all. Maximum speed. Best for game jams, prototypes, or if the reviews feel like overhead.

Write the choice to `production/review-mode.txt` immediately after the user
selects — no separate "May I write?" needed, as the write is a direct
consequence of the selection:
- `Full` → write `full`
- `Lean (recommended)` → write `lean`
- `Solo` → write `solo`

Create the `production/` directory if it does not exist.

---

## Phase 4: Confirm Before Proceeding

After presenting the recommended path, ask which step to take unless their existing
request already authorizes that step. For explicit tooling setup, continue through
the complete `/setup-tool` workflow. Otherwise never execute a suggested next step
without user authorization.

- **Prompt**: "Would you like to start with [recommended first step]?"
- **Options**:
  - `Yes, let's start with [recommended first step]`
  - `I'd like to do something else first`

---

## Phase 5: Hand Off

If the request already includes tooling setup work, perform the authorized `/setup-tool`
workflow and report actual results. For recommendation-only onboarding, when the
user confirms their next step, respond with a single short line: "Type `[skill command]` to begin." Nothing else. Do not re-explain the skill or add encouragement. The `/start` skill's job is done.

Verdict: **COMPLETE** — user oriented and handed off to next step.

---

## Edge Cases

- **User picks D but project is empty**: Gently redirect — "It looks like the project is a fresh template with no artifacts yet. Would Path A or B be a better fit?"
- **User picks A but project has code**: Mention what you found — "I noticed there's already code in `src/`. Did you mean to pick D (existing work)?"
- **User is returning (engine configured, concept exists)**: Skip onboarding entirely — "It looks like you're already set up! Your engine is [X] and you have a game concept at `design/gdd/game-concept.md`. Review mode: `[read from production/review-mode.txt, or 'lean (default)' if missing]`. Want to pick up where you left off? Try `/sprint-plan` or just tell me what you'd like to work on."
- **User doesn't fit any option**: Let them describe their situation in their own words and adapt.

---

## Collaborative Protocol

1. **Ask first** — never assume the user's state or intent
2. **Present options** — give clear paths, not mandates
3. **User decides** — they pick the direction
4. **Scoped execution** — recommendations need authorization; an existing request for setup/implementation already supplies that scope
5. **Adapt** — if the user's situation doesn't fit a template, listen and adjust

For libGDX onboarding use `/setup-engine libgdx [version]`, the five-role routing
and `.claude/docs/libgdx-development.md`. The Java desktop/headless starter is an
optional authorized scaffold, not an automatic installation. Kotlin/KTX and other
backends need explicit choices and verified toolchains.

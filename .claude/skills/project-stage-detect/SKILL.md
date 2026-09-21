---
name: project-stage-detect
description: "Automatically analyze project state, detect stage, identify gaps, and recommend next steps based on existing artifacts. Use when user asks 'where are we in development', 'what stage are we in', 'full project audit'."
argument-hint: "[optional: role filter like 'programmer' or 'designer']"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Write
model: haiku
# Read-only diagnostic skill — no specialist agent delegation needed
---

# Project Stage Detection

This skill scans your project to determine its current development stage, completeness
of artifacts, and gaps that need attention. It's especially useful when:
- Starting with an existing project
- Onboarding to a codebase
- Checking what's missing before a milestone
- Understanding "where are we?"

---

## Workflow

### 0. Resolve project kind and explicit state first

Run `python3 tools/ccgs_codex.py project-kind`; use the shared JSON and read the
contract/evidence it names. `conflict` is a configuration blocker: report actionable
paths and stop classification; do not fall back to a guessed stage or write state.
Valid kind/stage inconsistencies remain visible and require scoped resolution.
Read `.claude/docs/tooling-projects.md` for the exact contract.

For standalone tooling, report **Tooling Project** only when explicit compatible
stage exists, otherwise “tooling candidate / stage not configured” and recommend
`/setup-tool`. Report gaps separately: meaningful contract sections, usage/runtime
pins, actual owned tool source, representative fixtures, units/CLI integration,
independent review, current ADR dependencies, and saved resume task. Validate evidence
paths and actual results; adapter tests and example files are not this target's test
coverage. Do not calculate a completion percentage from file counts or invent a
Concept/Production/Polish transition. GDD, fun, art bible and game-engine gates are
N/A with a reason for a genuinely standalone agnostic tool. Use this tooling report
instead of the game heuristic/completeness sections below; preserve approval before
writing a report. Missing/incomplete spec → `/setup-tool update` or author/adopt;
missing implementation → lead/pipeline role; evidence gaps → actual tests/code review.

Game projects (including tool components) continue below with their explicit stage
preserved and tool gaps listed separately. Unknown pristine templates retain Concept
onboarding as a recommendation; classification itself never writes stage/kind.

### 1. Scan Key Directories

Analyze project structure and content:

**Design Documentation** (`design/`):
- Count GDD files in `design/gdd/*.md`
- Check for game-concept.md, game-pillars.md, systems-index.md
- If systems-index.md exists, count total systems vs. designed systems
- Analyze completeness (Overview, Detailed Design, Edge Cases, etc.)
- Count narrative docs in `design/narrative/`
- Count level designs in `design/levels/`

**Source Code** (`src/`):
- Count actual source files (language-agnostic, including `.js`, `.ts`, `.mjs` web modules and `.java`, `.kt` JVM files) under `src/` or explicit adopted source roots. For libGDX include actual `core/src`, `lwjgl3/src`, `headless/src` and selected platform modules; use the read-only `source-files` diagnostic and inspect custom Gradle sourceSets. Exclude `src/test` as well as bundled examples/templates, generated/build/vendor output. Core is shared code, not proof of a runnable backend.
- Exclude `templates/`, `.claude/docs/templates/`, `node_modules/`, `dist/`, generated output, caches and test trees from game-code evidence, even if they contain nested `src/`. Installing bundled templates never promotes stage.
- For web projects compare configured technical preferences with package/lockfile evidence. Dependencies alone are an engine candidate, not a configured engine. Report source roots and uncertainty for monorepos; retain `production/stage.txt` as the explicit override.
- Identify major systems (directories with 5+ files)
- Check for core/, gameplay/, ai/, networking/, ui/ directories
- Estimate lines of code (rough scale)

**Production Artifacts** (`production/`):
- Check for active sprint plans
- Look for milestone definitions
- Find roadmap documents

**Prototypes** (`prototypes/`):
- Count prototype directories
- Check for READMEs (documented vs undocumented)
- Assess if prototypes are archived or active

**Architecture Docs** (`docs/architecture/`):
- Count ADRs (Architecture Decision Records)
- Check for overview/index documents

**Tests** (`tests/`):
- Count test files
- Estimate test coverage (rough heuristic)

### 2. Classify Project Stage

Based on scanned artifacts, determine stage. Check `production/stage.txt` first —
if it exists, use its value (explicit override from `/gate-check`). Otherwise,
auto-detect using these heuristics (check from most-advanced backward):

| Stage | Indicators |
|-------|-----------|
| **Tooling Project** | Standalone-tool branch above; explicit compatible stage, gaps tracked separately |
| **Concept** | No game concept doc, brainstorming phase |
| **Systems Design** | Game concept exists, systems index missing or incomplete |
| **Technical Setup** | Systems index exists, engine not configured |
| **Pre-Production** | Engine configured, actual source roots have <10 implementation files |
| **Production** | actual source roots have 10+ implementation files, active development |
| **Polish** | Explicit only (set by `/gate-check` Production → Polish gate) |
| **Release** | Explicit only (set by `/gate-check` Polish → Release gate) |

### 3. Collaborative Gap Identification

**DO NOT** just list missing files. Instead, **ask clarifying questions**:

- "I see combat code (`src/gameplay/combat/`) but no `design/gdd/combat-system.md`. Was this prototyped first, or should we reverse-document?"
- "You have 15 ADRs but no architecture overview. Should I create one to help new contributors?"
- "No sprint plans in `production/`. Are you tracking work elsewhere (Jira, Trello, etc.)?"
- "I found a game concept but no systems index. Have you decomposed the concept into individual systems yet, or should we run `/map-systems`?"
- "Prototypes directory has 3 projects with no READMEs. Were these experiments, or do they need documentation?"

### 4. Generate Stage Report

Use template: `.claude/docs/templates/project-stage-report.md`

**Report structure**:
```markdown
# Project Stage Analysis

**Date**: [date]
**Stage**: [Concept/Systems Design/Technical Setup/Pre-Production/Production/Polish/Release/Tooling Project/unconfigured tooling candidate]
**Stage Confidence**: [PASS — clearly detected / CONCERNS — ambiguous signals / FAIL — critical gaps block progress]

## Completeness Overview
- Design: [X%] ([N] docs, [gaps])
- Code: [X%] ([N] files, [systems])
- Architecture: [X%] ([N] ADRs, [gaps])
- Production: [X%] ([status])
- Tests: [X%] ([coverage estimate])

## Gaps Identified
1. [Gap description + clarifying question]
2. [Gap description + clarifying question]

## Recommended Next Steps
[Priority-ordered list based on stage and role]
```

### 5. Role-Filtered Recommendations (Optional)

If user provided a role argument (e.g., `/project-stage-detect programmer`):

**Programmer**:
- Focus on architecture docs, test coverage, missing ADRs
- Code-to-docs gaps

**Designer**:
- Focus on GDD completeness, missing design sections
- Prototype documentation

**Producer**:
- Focus on sprint plans, milestone tracking, roadmap
- Cross-team coordination docs

**General** (no role):
- Holistic view of all gaps
- Highest-priority items across domains

### 6. Request Approval Before Writing

**Collaborative protocol**:
```
I've analyzed your project. Here's what I found:

[Show summary]

Gaps identified:
1. [Gap 1 + question]
2. [Gap 2 + question]

Recommended next steps:
- [Priority 1]
- [Priority 2]
- [Priority 3]

May I write the full stage analysis to production/project-stage-report.md?
```

Wait for user approval before creating the file.

---

## Example Usage

```bash
# General project analysis
/project-stage-detect

# Programmer-focused analysis
/project-stage-detect programmer

# Designer-focused analysis
/project-stage-detect designer
```

---

## Follow-Up Actions

After generating the report, suggest relevant next steps:

- **Concept exists but no systems index?** → `/map-systems` to decompose into systems
- **Missing design docs?** → `/reverse-document design src/[system]`
- **Missing architecture docs?** → `/architecture-decision` or `/reverse-document architecture`
- **Prototypes need documentation?** → `/reverse-document concept prototypes/[name]`
- **No sprint plan?** → `/sprint-plan`
- **Approaching milestone?** → `/milestone-review`

---

## Collaborative Protocol

This skill follows the collaborative design principle:

1. **Question First**: Ask about gaps, don't assume
2. **Present Options**: "Should I create X, or is it tracked elsewhere?"
3. **User Decides**: Wait for direction
4. **Show Draft**: Display report summary
5. **Get Approval**: "May I write to production/project-stage-report.md?"

**Never** silently write files. **Always** show findings and ask before creating artifacts.

# Upstream Issue Remediation Implementation Plan

> Implementation record: implement and independently review each task sequentially, with phase-specific evidence before integration. Release and CI verification are separate from local acceptance.

**Goal:** Resolve confirmed inherited defects from all 34 open upstream issues, with a full disposition matrix and tested public beta update.
**Architecture:** Direct source corrections plus regenerated Codex adapters; unchanged original lock and explicit reviewed-patch provenance; a small bounded ADR reader.
**Tech Stack:** Python 3.10+ standard library, Markdown, existing Bash hooks, GitHub Actions.
**Spec:** docs/superpowers/specs/2026-09-21-upstream-issues.md

## Global Constraints

- Python 3.10+ standard library only for adapter runtime; no global installs or permission bypass.
- Keep all 73 original skills, 49 roles and all original engine/review branches; source corrections are documented, not compressed rewrites.
- Keep `.codex/upstream-lock.json` unchanged; test reviewed patches and unexpected drift separately.
- Do not import user-game contributions, advertising issues or unreviewed third-party executable scripts.
- Implement and review phases sequentially, run relevant tests after each phase, then full suite and generated-integrity checks.
- Workers do not spawn subagents, publish or change trust. Controller owns delegation, final integration and public updates.

## Review Focus

1. Reviewed patch metadata cannot bless a different baseline or unsafe/out-of-root path; phase 1 tests these.
2. Approval denial or missing signoff cannot be bypassed by hotfix urgency or inherited broad authorization; phase 2 pins ordering and phase 5 samples behavior.
3. Huge single-line ADR sections, fenced fake headings, missing required sections, ambiguous statuses, stale provenance and multiple ADRs cannot become silent success; phase 3 tests these.
4. A runnable sprint goal needs scenes/assets/integration prerequisites as well as logic; phase 4 tests existing, scheduled and absent dependencies.
5. Safe upgrade advice must preserve customized files and Codex adapters even without shared history; phase 4 includes fixture-based dry-run evidence or precise manual checks, never a destructive automatic merge.

### Task 1: Reviewed source-patch integrity

**Files:** tools/ccgs/provenance.py (new), tools/ccgs/cli.py, tests/codex_adapter/test_provenance.py (new), .codex/upstream-patches.json (new empty ledger), docs/codex-adapter/source-maintenance.md (new).
**Consumes:** original lock `files` dictionary of path to SHA256; existing `upstream_drift(root)` CLI integration.
**Produces:** `verify_upstream(root, pristine=False) -> list[str]`; `upstream_drift(root)` delegates to it. `check --strict-upstream` accepts exact reviewed patches; `check --pristine-upstream` rejects every changed baseline file. Doctor reports the distinction.

- [ ] Write failing fixtures for pristine pass; reviewed change pass; unrecorded or wrong-hash change fail; wrong baseline hash/commit fail; duplicate/unknown/unsafe paths fail; missing source fail; pristine mode rejects a reviewed change. Keep existing CLI regression expectations intact.
- [ ] Implement schema version 1 ledger with baseline_commit matching the original lock's actual schema, and patches as a list of records containing path, original_sha256, patched_sha256, issue_urls (nonempty list), rationale (nonempty string). Validate types/hex digests and every record even when its source happens to match baseline. No automatic enrollment of changes.
- [ ] Implement the CLI flag and honest doctor scope, document the explicit recording procedure. Do not alter any original source in this task.
- [ ] Run targeted provenance/CLI tests then full adapter tests and strict check; record command/results, self-review and commit only task files.

### Task 2: Workflow order and consistency fixes

**Files:** .claude/skills/{hotfix,team-narrative,sprint-plan,architecture-decision}/SKILL.md; tests/codex_adapter/test_upstream_workflows.py (new); reviewed-patch ledger; generated adapters/inventory.
**Consumes:** phase 1 strict verification and explicit patch ledger.
**Produces:** source-level fixes for #69/#81 (duplicate), #86, #88 and #83 without losing phases or mode exceptions.

- [ ] Read the complete four source workflows and issue snapshot. Reproduce old ordering/missing checkpoint/contradictory wording/no outside-fence H1 with focused assertions before editing.
- [ ] In hotfix, separate read-only investigation/proposal from implementation; ask for approval covering proposed scope before any implementation spawn; retain actual LP/QA/producer signoff before release. Approval cancellation stops dependent work. Prior explicit authorization can satisfy the permission, not invent specialist signoff.
- [ ] Insert the narrative Phase 2/3 AskUserQuestion checkpoint with approve/revise/stop outcomes. Correct sprint Phase 2 feasibility claims to match original review mode and preserve coordinator responsibility. Resolve review mode once: an explicit --review flag must not be overwritten by the saved mode or a missing-file prompt; preserve the existing first-run choice only when no flag or saved setting exists. Insert a real skill-level H1 above the ADR template.
- [ ] Add ledger entries with baseline and current hashes + exact issue links; regenerate all adapters. Run focused workflow tests, full adapter suite, strict check and diff check; record and commit.

### Task 3: Bounded current ADR context and role routing

**Files:** tools/ccgs/adr.py (new), tools/ccgs/cli.py, tests/codex_adapter/test_adr.py (new); .claude/skills/{dev-story,create-stories,story-readiness}/SKILL.md; tools/ccgs/generate.py; docs/codex-adapter/runtime.md; tests/codex_adapter/test_catalog.py; ledger and generated outputs.
**Consumes:** current original ADR/story formats; same source hashes used by provenance; source refs remain project-relative.
**Produces:** `adr-context PATH` CLI with metadata-only mode, repeatable section selection and bounded character pagination, returning source hash/current status/section ranges/content/more-or-next cursor. Exact helper API may be chosen by worker and documented in report before later tasks use it.

- [ ] Write failing behavioral tests for huge single-line content, nested and numbered headings, code fences containing fake headings/statuses, multiple current-status declarations, missing requested sections, unsafe/outside paths, invalid pagination, complete reconstruction across pages and changed file hashes. No fixed 25k token assumption; use an explicit conservative character limit and honest pagination.
- [ ] Implement index/metadata extraction and bounded section reads using standard library. Missing or conflicting source facts are explicit, not an Accepted default. Include active amendments when relevant; don't silently drop later sections.
- [ ] Add per-ADR source SHA256 fields to create-stories instructions. Dev-story must check each current ADR's existence/Accepted status/hash before trusting its embedded decision summary and implementation notes. Hash mismatch, missing provenance or unclear notes require fresh targeted sections, not whole-file retries or silent reuse. Story readiness checks the same evidence. Preserve the original missing-ADR STOP and N/A exceptions consistently.
- [ ] Explicitly route `agent:` metadata in generated Codex entries, keeping interactive user decisions with the coordinator when a role lacks the question tool. Preserve role restrictions, real delegation, parent model inheritance and small task context. Do not mechanically add Claude `context: fork` to all skills.
- [ ] Record #63/#64 fixes and #72 adaptation treatment in ledger/docs, regenerate, run new tests and full suite, record evidence and commit.

### Task 4: Sprint prerequisites, safe updating and operating guidance

**Files:** .claude/skills/sprint-plan/SKILL.md, UPGRADING.md, docs/codex-adapter/{source-maintenance,operating-guide}.md, tests/codex_adapter/test_upstream_workflows.py, CCGS Skill Testing Framework/skills/{utility/hotfix,pipeline/dev-story}.md, ledger and generated outputs.
**Consumes:** previous workflow contracts and phase 1 patch ledger; maintain full/lean/solo semantics.
**Produces:** #58 runnable-goal dependency audit, #70 safe update guidance, explicit handling of #29/#46/#12 without pruning original capability.

- [ ] Reproduce missing runnable-prerequisite audit in sprint planning. Add goal→demonstration→required scenes/assets/services/tests→existing/scheduled/missing prerequisite mapping before story selection. Missing prerequisites must become in-sprint prerequisites, reduced goal or explicit defer/block; no invented runnable claim.
- [ ] Replace blanket unrelated-history merging and blind checkout advice with a clean-worktree/backup, baseline-aware diff and selective reviewed update path. Explain ordinary shared-history branch updates separately; never replace customized .claude wholesale. Include a concrete safe sequence and conflict handling.
- [ ] Document explicit delegated decision scope: authorization covers reversible in-scope choices with decision logs, not unapproved spend, publishing, missing input or fictional review evidence. Provide a small playable-loop recommendation retaining all tools, and a Unity-focused role/skill guide that leaves other engines available.
- [ ] Align the two affected inherited behavior specifications with canonical hotfix signoffs and dev-story implementation-only lifecycle, including the Config/Data exception, refusal behavior and ADR freshness/bounded reads. Keep useful scenarios and all framework files; record these reviewed source corrections. Align sprint Phase 6 review-mode descriptions with actual spawn/decision requirements.
- [ ] Record source patches, regenerate, run relevant tests then full suite and strict checks; record and commit.

### Task 5: Complete issue audit, behavioral acceptance and release

**Files:** docs/codex-adapter/upstream-issues-2026-09-21.md (all 34 issue dispositions), README-CODEX.zh-CN.md, .github/README.md, docs/codex-adapter/validation.md, RELEASE_NOTES.md, .github/workflows/codex-adapter.yml; behavior fixtures outside repo.
**Consumes:** all prior committed tests, patch ledger and current issue evidence.
**Produces:** public `v0.1.1-beta` with verified CI and complete human-readable acceptance record.

- [ ] Controller reconciles each open issue to evidence and disposition; duplicate issues share fix references. Features needing new engines/vendors/infrastructure remain clearly scoped requests, not mislabeled bugs. #56 is external DMF/Luau runtime code absent from this repository; verify that absence. #67 and #18/#24/#103 need actual Codex adaptation evidence, not claims based on counts.
- [ ] Run isolated fresh-agent scenarios for denied hotfix implementation, stale ADR summary plus very large current ADR, and missing sprint demonstration dependencies. Use actual tools and output artifacts; keep deterministic versus sampled evidence separate.
- [ ] Obtain whole-branch independent review; resolve actionable findings with tests and scoped re-review. Run full suite, generated integrity, strict reviewed baseline, original-lock hash equality and public diff review.
- [ ] Update public documents to distinguish baseline files from explicitly reviewed changes; do not keep the obsolete claim that every source file is untouched. Publish verified files against the fresh public head without force; retain user changes. Update beta release automation for v0.1.1-beta, verify CI and release assets before claiming completion.

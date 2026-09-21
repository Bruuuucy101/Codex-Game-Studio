# Upstream issue remediation design

Objective: audit upstream's open issues, identify inherited defects in Codex Game Studio and deliver tested updates. Work proceeds in phases, with tests after each phase. Release preparation does not modify upstream issues or account security/trust settings.

Authoritative snapshot at start: upstream commit 984023ddac0d5e27624f2baacde6105e45de375f; our public main 6b13261004ef72a3d11adae068349c400afb5a82. There are 34 open issues and 25 open PRs on upstream, and no open issues on our repository. PRs are reference material, not accepted fixes.

## Intended outcome

Retain every workflow, role, engine branch and review mode. Correct confirmed inherited workflow defects; make long-ADR loading bounded and current; eliminate contradictory approval/order instructions; improve dependency-aware sprint planning and update guidance. Public documentation must distinguish fixed, already handled, not inherited, unsupported environment, broad feature request and insufficient reproduction. All 34 issues receive a reasoned disposition; this is not a promise to implement every proposed new engine or paid vendor integration.

## Design decisions

Use direct, reviewable edits to the original workflow source, then regenerate adapters. Keep the 417-file original lock unchanged. Add a small reviewed-patch ledger recording each changed path's original hash, current approved hash, issue links and rationale. Strict verification accepts exactly the pinned source or an explicitly recorded patch; unlisted edits, stale patch hashes, unsafe paths and altered baseline associations fail. An explicit pristine check continues to prove original byte equality where needed. Do not silently reset the original lock.

Hotfix: separate read-only diagnosis/proposal from implementation, require authorized scope before writing code, and keep post-implementation lead/QA/producer validation before deployment/merge. Existing explicit user authorization satisfies repeated write prompts, but must not fabricate review verdicts or supersede a narrower restriction.

Narrative: restore the missing Phase 2 to 3 decision checkpoint. Sprint modes: retain full/lean/solo semantics and name who performs feasibility checks when producer review is skipped. Add a goal dependency audit that distinguishes already existing prerequisites, work scheduled earlier in the same sprint, missing prerequisites and explicitly deferred goals.

ADR context: provide a standard-library CLI helper returning fresh source hashes, current acceptance status, section ranges and bounded section content. Ignore Markdown headings and status examples in code fences. Preserve nested subsections and amendment constraints. A story summary may replace re-reading ADR prose only when its per-ADR provenance hash matches the current Accepted source; otherwise read the current relevant sections in bounded chunks and reconcile. Manifest dates alone do not prove ADR freshness. No fabricated status, silent truncation or automatic acceptance of missing ADRs. New stories record source hashes; legacy stories fall back safely.

Role routing: translate original agent metadata explicitly in Codex entries. A coordinator retains user-question handling when a selected role cannot ask; no fork metadata is blindly pasted into incompatible hosts and no nonexistent role is simulated. Codex role models continue to inherit by default. Bounded task briefs avoid inherited whole-session context where the host permits.

Updating: replace unrelated-history merge advice with a version-aware, reviewable path. Never recommend wholesale overwriting customized .claude files. Distinguish updating this Codex adapter from importing selected upstream fixes. The engine-filter guide points users to relevant existing roles without deleting other capabilities.

## Constraints and verification

- Python 3.10+ standard library only for adapter runtime; no global installs or permission bypass.
- Keep all 73 original skills, 49 roles and all original engine/review branches; source corrections are documented, not compressed rewrites.
- Keep `.codex/upstream-lock.json` unchanged; test reviewed patches and unexpected drift separately.
- Do not import user-game contributions, advertising issues or unreviewed third-party executable scripts.
- Implement and review phases sequentially, run relevant tests after each phase, then full suite and generated-integrity checks.
- Exercise fresh-agent behavior for approval ordering and ADR freshness/large-document cases; label model observations separately from deterministic tests.
- Publish only a verified commit to existing public repository, preserving concurrent changes; publish beta release after CI passes. Never claim original upstream issues were closed by our work.

Acceptance evidence: a complete issue matrix, regression tests, phase test logs, explicit patch ledger, generated checks, independent review, sampled behaviors and public commit/release/CI links.

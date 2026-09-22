# Production integration release — design

Publish the reviewed overnight feature update as v0.3.0-beta after the board,
asset providers, NPC voice, local asset tools and creative workflow phases pass
their declared implementation and acceptance gates. This release extends the
existing source-preserving Codex adaptation; it does not certify all external
accounts or every original workflow.

## Global Constraints

- Version/tag is `v0.3.0-beta`, archive `Codex-Game-Studio-v0.3.0-beta.zip` with prefix `Codex-Game-Studio/`, checksum file `SHA256SUMS.txt`. Existing releases/tags remain unchanged.
- Preserve every original and v0.2.0-beta role/workflow identity and the byte-identical 417-file original lock. The four new workflow identities are board-sync, npc-voice, creative-tools and asset-produce: expected final inventory 78 workflows and 57 roles. Derive other counts from actual final files.
- Local unit, actual HTTP fixtures, file/race/crash tests, model/native runtime, sampled workflow behavior, cloud CI, paid provider/account, creative review and engine import are separate evidence. Report source revision, actual commands/results and explicit unavailable evidence. A successful fixture is not a live-account or artistic-quality claim.
- Release only the exact reviewed commit after its required CI jobs pass. Keep PR publication disabled, public-repository/main-only conditions, contents-write scoped to release job, and existing-tag/release protection. An inaccessible API is not evidence that a release is absent.
- Preserve original attribution/license and qualified third-party model/runtime rights. No credentials, personal filesystem paths, weights, build output, private job records, runtime caches or SDD scratch enter published source or archive.

## Deliverable and gate

Current quickstarts and operating guidance describe actual shipped CLI routes,
optional dependencies, preview/write distinctions and platform requirements.
Core studio commands remain usable without optional provider/model dependencies.
PixelLab UI/inpaint experimental decoder support, unavailable live accounts,
POSIX hard-link collection requirements, model/runtime compatibility and any
unverified engine imports are stated beside the relevant capability.

Update the existing issue audit with a dated v0.3.0 section and dispositions for
#82, #23, #14 and #40 without erasing historical evidence or claiming upstream
closure. Issue23 remains partial for deferred GUI/Atlas and other uncovered
contribution features; enumerate its delivered subsets. No new feature is
advertised from a spec/plan alone. Current upstream snapshot remains34issues and
25PRs; our repository has no open issue and draftPR2, checked2026-09-22.

A concise production validation document links actual task/acceptance results
through portable evidence descriptions. Keep individual model photo probes,
local test fixtures and disconnected native MCP observations clearly scoped.
The original lock, reviewed patch ledger and generated manifests remain the
source-preservation evidence; do not refresh them to conceal unexpected drift.

Controller verifies final committed source against the candidate remote tree,
required candidate CI, main commit/tree after authorized merge, final main CI,
release tag/target and downloaded release archive/checksum. The archive must
match git archive semantics including binary bytes and executable modes.
Only then may final publication be called complete. An unavailable paid service
is a documented external acceptance limitation, not a fabricated pass. A real
failure in shipped required functionality must be fixed or explicitly excluded
from shipped claims before release.

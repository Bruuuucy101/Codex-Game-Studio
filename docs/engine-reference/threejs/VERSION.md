# Three.js — Version Reference

Last verified: 2026-09-21 (official source inspection; browser acceptance NOT RUN in Task 1).

| Field | Value |
|---|---|
| Canonical engine ID | `threejs` |
| Reference baseline candidate | 0.186.0 (r186) |
| Project pin | Read the adopted project's package.json and package-lock.json; this framework is unconfigured |
| Documentation verified | 2026-09-21 |
| Risk | Exact installed release required; mutable docs can differ |

The version above is the selected scaffold candidate, not a claim of runtime verification or newest release. Preserve an existing project pin. r187 is unreleased at this verification date; the 186 → 187 migration section must not be applied to r186. Pin @types/three to 0.186.0 and use addons from the same three package.

Consult [breaking changes](breaking-changes.md), [API cautions](deprecated-apis.md), [practices](current-best-practices.md) and relevant modules before making recommendations. Missing pin or undocumented API: request tagged-source verification through setup/coordinator.

## Verified official sources

- [Tagged package metadata](https://raw.githubusercontent.com/mrdoob/three.js/r186/package.json)
- [Three.js releases](https://github.com/mrdoob/three.js/releases)

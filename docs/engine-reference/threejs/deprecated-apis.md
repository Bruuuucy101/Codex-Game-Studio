# Three.js API cautions

Last verified: 2026-09-21.

The migration guide's 182 → 183 section deprecates Clock in favor of Timer. Consult tagged Timer semantics before replacing a project clock; a pure simulation may instead receive an explicit fixed time step. Legacy Geometry examples must be adapted to the installed BufferGeometry API. Avoid mixing addon revisions and do not apply future r187 removals to r186.

This is a curated warning list; inspect project usage and official transition notes rather than claiming complete API coverage.

Sources: [migration guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide), [r186 Timer](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/core/Timer.js), [r186 package exports](https://raw.githubusercontent.com/mrdoob/three.js/r186/package.json).

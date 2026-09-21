# Three.js revision boundaries

Last verified: 2026-09-21.

The candidate is npm 0.186.0 / r186. The official migration guide already contains a 186 → 187 section, including future PMREM/mapping and viewport behavior changes; r187 is unreleased at this date. Do not describe those changes as r186 behavior. Use tagged r186 source to resolve ambiguity.

The 185 → 186 transition introduces Object3D.dispose. It does not remove the need to dispose owned geometry, material and texture resources separately. WebGLRenderer requires WebGL2; WebGL1 support ended at r163.

Sources: [migration guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide), [r186 Object3D](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/core/Object3D.js), [r186 WebGLRenderer](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/renderers/WebGLRenderer.js).

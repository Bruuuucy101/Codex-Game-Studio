# Three.js rendering, assets and input

Last verified: 2026-09-21.

WebGLRenderer uses WebGL2 in r186. WebGPU is separate opt-in scope. Import addons from the installed three/addons path so revision and renderer assumptions agree. Update camera projection when aspect changes and set renderer size/pixel ratio deliberately; cap rendering cost for high-DPI devices. Texture color space follows its data semantics; consult the pin before changing output/tone mapping.

Three.js supplies rendering, not a complete physics/gameplay/UI stack. Keep pure state apart from meshes and DOM HUD. Convert pointer coordinates to canvas space for picking, clear held keys on blur/visibility loss, release pointer capture on cancellation, and preserve DOM focus/accessibility. Treat unsupported graphics and failed loads as visible recoverable states.

Sources: [r186 renderer](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/renderers/WebGLRenderer.js), [r186 package/addon exports](https://raw.githubusercontent.com/mrdoob/three.js/r186/package.json), [browser autoplay](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay).

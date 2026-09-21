# Three.js resource lifecycle

Last verified: 2026-09-21.

Own exactly one loop. Stop it with setAnimationLoop(null), or cancel the owned requestAnimationFrame callback, before destroying the application. Remove DOM/window listeners and dispose controls. Guard late async loader completion after teardown.

In r186 Object3D.dispose dispatches a disposal event; geometry, material and texture resources may be shared and are separate. scene.clear only removes children. Track an ownership set or reference counts: dispose each owned geometry, material, texture and render target after its final user releases it; material disposal does not release textures. Dispose the renderer when the application ends. Resetting gameplay should not construct a second renderer/loop. Make repeated teardown safe.

Sources: [r186 Object3D](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/core/Object3D.js), [r186 Material](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/materials/Material.js), [r186 Texture](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/textures/Texture.js), [r186 renderer](https://raw.githubusercontent.com/mrdoob/three.js/r186/src/renderers/WebGLRenderer.js).

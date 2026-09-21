# Graphics and resource ownership

Checked 2026-09-21; libGDX 1.14.2.

Choose GL/GL ES capability from selected backends and devices. SpriteBatch,
ModelBatch, shaders, textures, meshes and framebuffers need explicit ownership
and render-thread use. Shared assets follow manager ownership; direct temporary
allocations are released by their creator.

Keep begin/end balanced, preserve transparency ordering, and measure flushes
before sorting/atlasing changes. FBO transitions and resize require deliberate
viewport/camera restoration and attachment replacement. Check shader compile
logs and target-device results; the headless backend cannot validate them.

The starter desktop module draws generated shapes and a localized text HUD.
Its installDist acceptance compiles/packages desktop code; it does not establish
render quality, audio, mobile drivers or performance.

Sources: [SpriteBatch](https://libgdx.com/wiki/graphics/2d/spritebatch-textureregions-and-sprites),
[framebuffers](https://libgdx.com/wiki/graphics/opengl-utils/frame-buffer-objects),
[threading](https://libgdx.com/wiki/app/threading).

# Scene2D and Scene2D.ui

Checked 2026-09-21, reference target 1.14.2.

A Stage provides scene graph traversal, input dispatch and drawing. Table/Skin
supply layout/style conventions; the UI owner still defines navigation,
localization, modal behavior and accessibility. Update the Viewport on resize
and test supported dimensions, focus transitions and processor ordering.

Custom Actor.draw(Batch, float) is valid. Stage has already begun the batch;
respect parent alpha and drawing state. Layout data changes need appropriate
invalidation. Manage act/draw timing and hidden-screen input explicitly.

Stage disposes a batch it created; when given an external batch, ownership stays
external. Establish Skin/atlas/manager ownership separately and do not double
release shared assets. Headless mocks do not verify clipping, text or layout.

Sources: [Scene2D.ui](https://libgdx.com/wiki/graphics/2d/scene2d/scene2d-ui),
[Actor source](https://github.com/libgdx/libgdx/blob/1.14.2/gdx/src/com/badlogic/gdx/scenes/scene2d/Actor.java),
[Stage source](https://github.com/libgdx/libgdx/blob/1.14.2/gdx/src/com/badlogic/gdx/scenes/scene2d/Stage.java).

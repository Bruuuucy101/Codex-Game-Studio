# Phaser 3 rendering, assets and input

Last verified: 2026-09-21.

Choose AUTO/WebGL/Canvas explicitly for the project, verify the actual renderer and target browser, and coordinate viewport scaling with camera/input coordinates. Profile texture memory, batching and redraw costs. Handle loader errors instead of beginning with missing assets. Shared texture/audio caches need named owners.

Keyboard state must clear on blur and visibility loss; pointer cancellation must release held input. Canvas rendering does not create accessible DOM controls: use ui-programmer for HTML/CSS/focus/labels. Gesture-start audio and test deployed asset paths, CORS and high-DPI resize on target browsers.

Sources: [Phaser concepts](https://docs.phaser.io/phaser/concepts), [Phaser scene lifecycle](https://docs.phaser.io/phaser/concepts/scenes), [browser autoplay](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay).

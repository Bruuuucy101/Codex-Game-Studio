# Shared AssetManager ownership

Checked 2026-09-21; libGDX 1.14.2.

Define a manager owner and each consumer's load/unload claim. Wait for completion
before get; report loader errors. Async load completion must not revive an
inactive screen. Shared textures/sounds retrieved from a manager are not each
screen's private disposable resources. Release claims through the owner and
unload lifecycle; dispose the manager at its final application boundary.

Private resources created directly (for example the starter's font/batch/shapes)
have their own owner and deterministic disposal. Avoid mixing both schemes for
the same resource. Review screen retention separately: Game.setScreen hides the
old screen but does not automatically dispose it.

Sources: [asset management](https://libgdx.com/wiki/managing-your-assets),
[AssetManager source](https://github.com/libgdx/libgdx/blob/1.14.2/gdx/src/com/badlogic/gdx/assets/AssetManager.java),
[Game source](https://github.com/libgdx/libgdx/blob/1.14.2/gdx/src/com/badlogic/gdx/Game.java).

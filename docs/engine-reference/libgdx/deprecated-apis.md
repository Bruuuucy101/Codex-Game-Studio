# libGDX deprecated and mistaken API guidance

Checked 2026-09-21 against libGDX 1.14.2. Inspect @Deprecated and release notes
for the project's actual source version; this page is not a complete inventory.

| Proposal or assumption | Correction |
|---|---|
| Never implement Actor.draw | A custom draw(Batch, float) override is supported; respect Stage's active batch and parent alpha. |
| Game.setScreen disposes the previous screen | It hides it; the game owner chooses when to dispose. |
| Dispose every shared texture on screen change | Release that screen's manager claims; do not directly dispose a shared managed object. |
| Enable headless LWJGL3 | Depend on gdx-backend-headless and instantiate HeadlessApplication. |
| libktx is another engine | Configure Kotlin/KTX explicitly within libgdx, with verified compatible pins. |

Sources: [Actor 1.14.2](https://github.com/libgdx/libgdx/blob/1.14.2/gdx/src/com/badlogic/gdx/scenes/scene2d/Actor.java),
[Game 1.14.2](https://github.com/libgdx/libgdx/blob/1.14.2/gdx/src/com/badlogic/gdx/Game.java),
[headless backend](https://github.com/libgdx/libgdx/tree/1.14.2/backends/gdx-backend-headless),
[KTX project](https://github.com/libktx/ktx).

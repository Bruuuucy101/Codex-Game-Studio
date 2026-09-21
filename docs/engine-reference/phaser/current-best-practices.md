# Phaser 3 project practices

Last verified: 2026-09-21. Curated guidance, not a complete API snapshot or executed acceptance.

Keep pure fixed-step state in `src/core/`, engine adapters in `src/scenes/`, input and DOM HUD in their owned modules, and balance data in `assets/data/game.json`. Read installed pins before copying examples. Reuse accepted project architecture; no implicit framework, physics, service-worker or network dependency.

Use [lifecycle](modules/lifecycle.md), [rendering/assets/input](modules/rendering-assets-input.md) and [testing](modules/testing.md). Shared toolchain and browser constraints are in [.claude/docs/web-game-development.md](../../../.claude/docs/web-game-development.md).

Official source context: [tagged package](https://raw.githubusercontent.com/phaserjs/phaser/v3.90.0/package.json). Application architecture here is a studio convention.

# Phaser 3 lifecycle and ownership

Last verified: 2026-09-21.

`init`, `preload`, `create`, `update` define the scene run. Load assets before creating consumers. `SHUTDOWN` on stop/restart differs from final `DESTROY`. Clean up owned DOM/window/global event subscriptions and external timers on shutdown; make the cleanup idempotent and register per-run handlers in create. Do not double-destroy scene-managed objects. A final application owner destroys the Game and removes its canvas. Avoid late callbacks changing stopped scenes and do not remove shared cache entries while another scene uses them.

The engine does not promise deterministic network lockstep merely because Arcade/Matter physics is selected. Keep deterministic simulation and test clocks separate from browser rendering.

Official source: [Scenes lifecycle and shutdown/destroy](https://docs.phaser.io/phaser/concepts/scenes). Ownership and testing conventions are project guidance.

# Optional Ashley ECS and Box2D

Checked 2026-09-21. Neither dependency is enabled in the Java starter. Verify the
selected Ashley and Box2D artifacts/versions before writing version-specific code;
do not derive Ashley's version from libGDX 1.14.2.

Separate component data from ordered systems and document Family/mapper ownership.
PooledEngine is a choice with reset/stale-reference obligations, not a default
requirement. Match allocation strategy to measurements.

A Box2D World owns native simulation resources. Choose meters/pixels conversion,
fixed step and bounded catch-up explicitly. Contact callbacks must not mutate a
locked World; queue structural changes to a safe point. Test native lifetimes and
collision filters on the selected backend. Fixed step alone does not certify
cross-platform deterministic multiplayer.

Sources: [Ashley](https://github.com/libgdx/ashley),
[Box2D guide](https://libgdx.com/wiki/extensions/physics/box2d),
[World 1.14.2](https://github.com/libgdx/libgdx/blob/1.14.2/extensions/gdx-box2d/gdx-box2d/src/com/badlogic/gdx/physics/box2d/World.java).

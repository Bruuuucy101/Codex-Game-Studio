# Phaser 3 version boundaries

Last verified: 2026-09-21.

The candidate is 3.90.0. Do not substitute Phaser 4 even when a latest-version search returns it. Audit actual source/lockfile and official release notes before changing 3.x pins; this curated reference makes no exhaustive migration claim.

A restart invokes scene shutdown and another run of the scene lifecycle; final destroy is a separate event. Register/release external resources per run. Concurrent scenes are supported; a single-screen scene convention is not an API restriction.

Sources: [3.90.0 metadata](https://raw.githubusercontent.com/phaserjs/phaser/v3.90.0/package.json), [release archive](https://phaser.io/download/archive), [scene lifecycle guide](https://docs.phaser.io/phaser/concepts/scenes).

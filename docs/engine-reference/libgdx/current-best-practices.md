# libGDX project practices

Last verified: 2026-09-21. Apply project ADRs and actual pins first.

Keep simulation data and rules independent of Gdx static state. Inject time/input,
load balance from assets/data, and test outcomes deterministically. Put backend
launchers and platform services in their own modules. Keep render-thread ownership
explicit; queue completed CPU work rather than touching GL from workers.

Track resource owners and screen transitions. Shared loading managers outlive
individual consumers; private render resources belong to their creator. Measure
allocations, frame timing, draw calls and memory before optimizing. Pooling adds
lifetime obligations and should answer an observed need.

Use exact dependency declarations and committed locks, verify the wrapper, and
separate pure tests, real headless lifecycle, desktop packaging, GPU playtests and
each optional platform. Document which layers have actual evidence.

Read the five module references. Sources:
[threading](https://libgdx.com/wiki/app/threading),
[memory management](https://libgdx.com/wiki/articles/memory-management),
[dependency locking](https://docs.gradle.org/8.14.3/userguide/dependency_locking.html).

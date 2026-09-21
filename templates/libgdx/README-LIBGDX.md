# libGDX collect starter

A small Java game: move the cyan player to the gold signal, then press R to reset.
The shared simulation has no Gdx/renderer dependency. Desktop graphics/input lives
in lwjgl3; headless runs the same game lifecycle with mock graphics/audio/input.
This is an extensible prototype, not a complete shipping UI/accessibility system.

## Pinned toolchain and modules

libGDX 1.14.2, Gradle 8.14.3, JUnit Jupiter 5.13.4 / Platform 1.13.4. Build with
JDK 21; Java source/API target is release 8. This does not promise that all current
transitive libraries or optional backends run on a Java 8 runtime. Existing
projects keep their verified toolchain unless a migration is explicitly chosen.

- core/src/main/java: immutable config, pure simulation and game/screen owner.
- core/src/test/java: deterministic movement, bounds, collect/reset and bad input.
- lwjgl3/src/main/java: desktop launcher, polled keyboard input and owned renderer.
- headless/src/main/java: finite scripted run and bounded HeadlessApplication runner.
- headless/src/test/java: real create/render/pause/dispose, collect/reset,
  repeated-run isolation, callback failure propagation and timeout shutdown.
- assets/: one balance source and text messages, packaged into the core JAR.

No Ashley, Box2D, Kotlin/KTX or mobile/browser module is selected. Those require
separate dependency, compiler/SDK and runtime validation. libktx is a choice within
libGDX, not another engine.

## Build and test

Set JAVA_HOME for this invocation to your verified JDK 21. Do not change global
machine settings. On macOS/Linux use the included executable wrapper:

```sh
./gradlew :core:test :headless:test :lwjgl3:installDist --no-daemon
./gradlew :headless:run --no-daemon
./gradlew :lwjgl3:run --no-daemon
```

On Windows use `gradlew.bat` with the same task names. The first use downloads the
checksum-pinned Gradle distribution and exact Maven dependencies; later offline
runs can use `--offline` with a populated cache. Hosts without a working filesystem
watcher can add `--no-watch-fs`. Tests do not require a GPU. A failed/absent runtime
is NOT RUN; never describe pure tests as backend execution.

`lwjgl3/build/install/lwjgl3/` contains the installed desktop launcher and its
library directory. Assets are classpath resources: launch from any working
directory. On macOS the `:lwjgl3:run` task sets `-XstartOnFirstThread`. The installed
Unix launcher needs `JAVA_OPTS=-XstartOnFirstThread` on macOS. Other platforms do not
need that option. Keep the entire distribution directory together.

Dependencies are locked per module. To deliberately change dependencies, inspect
new exact declarations and resolve all configurations using:

```sh
./gradlew resolveDependencyLocks --write-locks --no-daemon
```

Review the lock diffs, then rerun normal acceptance without `--write-locks`. Do not
regenerate locks merely to hide mismatches. Wrapper provenance/checksums are in
THIRD-PARTY-NOTICES.md.

## Controls, design and balance schema

Keyboard only in this prototype: WASD/arrows move; R resets position, score and
collectible. Movement caps diagonal magnitude, respects player-radius bounds and
uses swept target intersection so an accepted long step cannot skip the signal.
Collect once per round. Reset does not move in the same command. Time and input
are supplied to the simulation; no wall clock, randomness or static game state.

`assets/data/game_config.json` is the sole balance source. All fields are required:

| Field | Meaning |
|---|---|
| width, height | Positive world dimensions, 320 × 180 logical units |
| playerRadius, targetRadius | Positive collision/draw extents, 8 and 10 units |
| speed | Positive movement speed, 120 units/second |
| startX, startY | Player center, initially 60,60 inside world bounds |
| targetX, targetY | Signal center, initially 180,60 inside world bounds |
| fixedStep | Positive scripted headless step, approximately 1/60 second |
| maxDelta | Maximum accepted backend frame delta, 0.1 second |

All numbers must be finite; circles must fit bounds; fixedStep cannot exceed
maxDelta. Invalid data fails before play. This is schema version 1; changes to
field meanings require a documented migration. The desktop frame adapter caps
long stalls; this prototype does not claim network lockstep determinism. Text in
assets/i18n/messages.properties can be translated with additional bundle locales.

## Ownership and evidence boundaries

CollectGame owns its screen and explicitly disposes it (Game.dispose/setScreen do
not do that automatically). The desktop presentation privately owns font, batch
and shapes; headless creates none of them. No shared AssetManager is needed for
these small generated visuals. Add one only with a clear application owner and
consumer load/unload claims; never dispose a shared retrieved texture per screen.

HeadlessRunner serializes application runs, captures callback errors, requests
exit on timeout, joins the backend thread and restores the Gdx fields the backend
sets. Its bounded cleanup has a 2-second grace window. Callbacks must remain
nonblocking; Java cannot safely kill arbitrary uncooperative code. This runner
cannot coexist with another active Gdx application in the same process; use a
separate process for that case.

Actual headless tests validate lifecycle and simulation. Desktop installDist only
validates compilation/packaging. Before release, manually play on each chosen
graphics backend: move, collect, reset twice, resize, lose/regain focus, close;
inspect errors and resource behavior. GPU rendering, audio, touch/gamepad,
accessibility, mobile, GWT, Kotlin, Ashley and Box2D remain separate checks.

When copied into an existing studio, README.md/.gitignore/CLAUDE.md stay intact.
Ensure `.gradle/` and module `build/` outputs are ignored in your own project; keep
wrapper scripts/JAR/properties, source and gradle.lockfile under version control.

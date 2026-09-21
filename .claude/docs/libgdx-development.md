# libGDX development contract

Canonical engine ID is `libgdx`. `/setup-engine libgdx [version]` records the
actual Java or Kotlin language, selected backends, Gradle/JDK versions, dependency
pins, source roots and reference import. `libktx` is an alias requesting a
Kotlin/KTX choice inside libGDX; it requires independently verified plugin/KTX
versions and backend compatibility. Never guess those pins or claim Java tests
executed Kotlin. Existing adopted project pins take precedence over this starter.

## Roles and workflow

The lead `libgdx-specialist` reports through lead-programmer to technical-director.
It delegates Scene2D/Stage/Table/Skin/input layout to libgdx-scene2d-specialist;
batches/shaders/FBOs to libgdx-graphics-specialist; selected Ashley/Box2D ECS,
stepping and contacts to libgdx-ashley-specialist; lifecycle/AssetManager/platform
APIs/Gradle/backends to libgdx-core-specialist. All are real roles with complete
canonical and generated native profiles. Existing programmer, art/UI, QA and
build owners remain responsible for implementation and review. Preserve the
selected full/lean/solo gates; do not self-simulate required delegated reviews.

Route by actual subsystem/path/imports, with lead fallback for ambiguous Java or
Kotlin. `rg --glob '*.java' --glob '*.kt'` avoids ripgrep type assumptions. Read
VERSION, breaking/deprecated guidance and the relevant reference module first.
Optional ECS/physics is not automatically required by this engine choice.

## Source roots and rules

Inspect Gradle settings and sourceSets read-only before running a build. Conventional
roots are src/, core/src, lwjgl3/src, headless/src and selected desktop/android/ios/html
modules. The read-only `python3 tools/ccgs_codex.py source-files` command lists
implementation files in these roots; use `--root PATH` before the subcommand for
an adopted project. Custom sourceSets need explicit inspection. Exclude templates,
examples, tests, generated/build/vendor output and dependencies. A bundled template
or engine reference never makes a pristine studio an active game.

Keep package responsibility explicit: gameplay/, ui/, core/, ai/, networking/ under
actual module src/main roots retain the matching rules. Gradle src/test roots
receive test standards; assets/data remains the balance source. Inspect rule
matches with `rules PATH...`, also before shell-created files. For differently
named adopted packages, map their actual responsibilities to rules during setup;
do not treat an unmatched package as permission to ignore standards.

## Safe starter handoff

The included Java candidate is libGDX 1.14.2, Gradle 8.14.3, build JDK21, release8
source target, JUnit Jupiter5.13.4 / Platform1.13.4. It provides core/lwjgl3/headless,
a data-driven collect loop and localized text. It does not select mobile/GWT,
Kotlin/KTX, Ashley or Box2D. All require separately reviewed SDK/dependency evidence.

An authorized tools-programmer/core specialist runs:

```sh
python3 tools/ccgs_codex.py scaffold-libgdx --target PATH
python3 tools/ccgs_codex.py scaffold-libgdx --target PATH --write
```

Preview is read-only. The explicit manifest includes SHA256, bytes and modes;
copy preserves the real wrapper JAR and executable Unix script. Collisions,
symlink paths, traversal and protected metadata are rejected before writing.
README.md/.gitignore/CLAUDE.md stay intact. Copy neither installs dependencies
nor configures the engine. Do not bypass refusal or silently replace existing
module/build files. The caller still observes host filesystem/network permissions.

The wrapper scripts and embedded JAR license retain official provenance; see
`templates/libgdx/THIRD-PARTY-NOTICES.md`. No build cache/JDK/native binaries ship
with the template. Build/dependency setup is an explicit separate operation.

## Actual acceptance and limits

From a clean copied target under the configured JDK:

```sh
./gradlew :core:test :headless:test :lwjgl3:installDist --no-daemon
./gradlew :headless:run --no-daemon
```

Windows uses gradlew.bat. Use --no-watch-fs when the host cannot start a watcher;
use --offline only with a populated cache. Record versions, source manifest,
lockfiles, commands and actual XML results. Strict dependency locks cover all
resolved runtime/test configurations. Refresh only on a deliberate dependency
change with `resolveDependencyLocks --write-locks`, then run acceptance without it.

Pure simulation tests and actual HeadlessApplication tests are distinct. The
runner bounds waiting, forwards callback failures, requests exit, joins the
backend and restores its Gdx globals after stop. Tests are serialized and repeat
applications; callback code must never block. The backend provides mock graphics,
audio and input, so it cannot prove layout, shaders, sound or device behavior.

Desktop installDist checks compilation and packaging. For a real desktop playtest
run :lwjgl3:run; on macOS the task supplies -XstartOnFirstThread. An installed
launcher requires JAVA_OPTS=-XstartOnFirstThread on macOS. Verify movement,
collection, reset twice, resize, focus/pause and clean exit/errors; inspect actual
frames. GPU playtests and optional backends remain NOT RUN until observed.
See docs/codex-adapter/validation.md for release evidence, not a promise that every
adopted environment passes. Keep existing Logic/Integration/Visual-Feel test gates.

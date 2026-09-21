# Lifecycle, Gradle and backends

Checked 2026-09-21. Starter pins: libGDX 1.14.2, Gradle 8.14.3, JUnit Jupiter
5.13.4 / Platform 1.13.4, build JDK 21, release 8 source target. Existing project
pins take precedence. Exact wrapper distribution checksum and JAR provenance
are shipped in templates/libgdx/THIRD-PARTY-NOTICES.md.

core owns common simulation; lwjgl3 owns desktop graphics/input and launch;
headless owns a real HeadlessApplication harness. Assets are classpath resources
from assets/, so launching an installed distribution does not require the source
working directory. No global JDK or machine configuration is changed.

Run `./gradlew :core:test :headless:test :lwjgl3:installDist --no-daemon`.
On Windows use gradlew.bat. Local hosts without filesystem watching can add
--no-watch-fs. Record java/Gradle versions and results, not just a command proposal.
Locks pin resolved transitive graphs; deliberate dependency updates resolve and
review locks before normal locked acceptance.

Headless uses mock graphics/audio/input. The harness captures background failures,
awaits bounded termination, closes callbacks and restores Gdx statics after stop.
Tests run serially; process isolation is an alternative. An uncooperative blocking
callback cannot be safely force-killed; never block backend callbacks.

Desktop macOS needs -XstartOnFirstThread (the Gradle run task supplies it; installed
launchers use JAVA_OPTS). Optional Android/iOS/GWT require separate SDK/compiler
checks; Kotlin/KTX requires an explicit verified stack. No automatic support claim.

Sources: [headless source](https://github.com/libgdx/libgdx/blob/1.14.2/backends/gdx-backend-headless/src/com/badlogic/gdx/backends/headless/HeadlessApplication.java),
[starter classes](https://libgdx.com/wiki/app/starter-classes-and-configuration),
[Gradle wrapper](https://docs.gradle.org/8.14.3/userguide/gradle_wrapper.html),
[dependency locks](https://docs.gradle.org/8.14.3/userguide/dependency_locking.html).

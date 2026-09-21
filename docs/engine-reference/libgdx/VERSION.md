# libGDX version context

- **Engine ID**: libgdx
- **Engine Version**: 1.14.2 (included Java starter candidate)
- **Project Pinned**: unconfigured; an adopted project's verified pin takes precedence
- **Last Docs Verified**: 2026-09-21
- **Risk Level**: HIGH — verify version-sensitive API details from tagged sources
- **Build JDK**: 21; local acceptance runtime is recorded in the validation evidence
- **Gradle**: 8.14.3 with official wrapper and SHA256-pinned distribution
- **Tests**: JUnit Jupiter 5.13.4 / Platform launcher 1.13.4
- **Starter Java target**: release 8 (build runs on JDK 21)
- **Included modules**: core, lwjgl3, headless
- **Optional, not runtime-certified**: Kotlin/KTX, Ashley, Box2D, Android, iOS, GWT

`libktx` is a language/extension choice within libGDX, not a second engine.
Do not infer optional dependency versions from the engine pin. Existing Java or
Kotlin projects retain their toolchain until an explicit migration is accepted.

## Sources and evidence

[libGDX 1.14.2 release](https://github.com/libgdx/libgdx/releases/tag/1.14.2),
[tagged source](https://github.com/libgdx/libgdx/tree/1.14.2),
[Gradle Java compatibility](https://docs.gradle.org/8.14.3/userguide/compatibility.html),
[wrapper verification](https://docs.gradle.org/8.14.3/userguide/gradle_wrapper.html).

The reference is a bounded curated snapshot, not an exhaustive API dump. See
`modules/` and `.claude/docs/libgdx-development.md`. Documentation checks are
separate from execution; `docs/codex-adapter/validation.md` records actual tests
and limits. A desktop distribution build is not a GPU or device playtest.

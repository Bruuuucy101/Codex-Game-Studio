# libGDX migration boundaries

Verified against 1.14.2 sources on 2026-09-21. This is a migration checklist,
not a claim that every historical release is compatible.

- Inspect the actual old/new release notes and Gradle dependency graph before
  changing a pin. Align gdx, selected backends and native artifacts; reconcile
  committed dependency locks as an explicit reviewed update.
- LWJGL2 and LWJGL3 use different launcher/configuration classes. A package/import
  rename alone does not establish input, window, audio or native compatibility.
- HeadlessApplication belongs to a separate backend; it is not a LWJGL3 flag.
- Build JDK and emitted bytecode/API target are distinct. Adding Android, RoboVM
  iOS, GWT or Kotlin changes compiler/SDK constraints; validate those independently.
- Verify lifecycle behavior during upgrades: retaining old screens is a project
  decision and shared asset lifetimes must still have one owner.

Sources: [versioned releases](https://github.com/libgdx/libgdx/releases),
[backend starters](https://libgdx.com/wiki/app/starter-classes-and-configuration),
[GWT limitations](https://libgdx.com/wiki/html5-backend-and-gwt-specifics).

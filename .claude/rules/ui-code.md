---
paths:
  - "src/ui/**"
  - "core/src/main/**/ui/**"
  - "lwjgl3/src/main/**/ui/**"
  - "headless/src/main/**/ui/**"
  - "desktop/src/main/**/ui/**"
  - "android/src/main/**/ui/**"
  - "ios/src/main/**/ui/**"
  - "html/src/main/**/ui/**"
---

# UI Code Rules

- UI must NEVER own or directly modify game state — display only, use commands/events to request changes
- All UI text must go through the localization system — no hardcoded user-facing strings
- Support both keyboard/mouse AND gamepad input for all interactive elements
- All animations must be skippable and respect user motion/accessibility preferences
- UI sounds trigger through the audio event system, not directly
- UI must never block the game thread
- Scalable text and colorblind modes are mandatory, not optional
- Test all screens at minimum and maximum supported resolutions

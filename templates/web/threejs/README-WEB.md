# Signal Field — threejs collect starter

A standalone TypeScript collect game with local primitive art and no network services.
Balance lives in `assets/data/game.json`. Arrow keys/WASD move; clicking the field
sets a destination. Gold diamonds are collectibles. Reset supports repeated play.

Use Node **22.14.0** (Vite requires at least 22.12 on the Node 22 line) and npm
10.9.2 for the recorded baseline. Direct dependency versions and the complete
resolved tree are pinned in package.json/package-lock.json.

```sh
npm ci
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:browser
```

`npm run dev` serves development locally. `npm run preview` serves the built
production bundle on `127.0.0.1:4173` with strict port ownership. Playwright starts
and stops its own preview process and refuses an already occupied port; build
before browser tests. Browser tests use actual keyboard/pointer input, record
screenshots in `test-results/`, and exercise two collect/reset cycles, focus loss,
resize, and errors. Three.js additionally requires an actual WebGL2 context.

`tests/web-unit/**/*_test.ts` is the isolated Vitest suite; `tests/browser` is
Playwright only. The production bundle exposes no test mutation interface.
`src/core` owns fixed stepping; `src/gameplay` owns state and input;
`src/scenes` owns engine rendering/lifecycle; `src/ui` displays state and sends
reset commands. Input is cleared when the field/window loses focus or the page
is hidden. Engine resources and listeners are disposed on teardown/HMR.

This copy command does not install dependencies or configure the studio engine.
Use `/setup-engine threejs` separately for version references and role routing.
Existing README.md, .gitignore and studio metadata are never replaced. For a
standalone directory, exclude node_modules/, dist/, test-results/ and
playwright-report/ from your own version control configuration.

Acceptance is Chromium desktop only when browser tests actually pass. Build/unit
success alone does not verify rendering. macOS host browser launch was blocked
in the authoring environment; Linux CI supplies the browser acceptance gate.
Safari, mobile, WebGPU, gamepad, audio and native hardware are outside this starter.

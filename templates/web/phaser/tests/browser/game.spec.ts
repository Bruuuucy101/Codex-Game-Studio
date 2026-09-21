import { expect, test } from '@playwright/test';

test('real input collects, resets twice, clears focus, and resizes a rendered game', async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto('/');
  const canvas = page.locator('#game canvas');
  const score = page.locator('#score');
  const position = page.locator('#position');
  await expect(canvas).toBeVisible();
  await expect(score).toHaveText('0 / 3');
  await expect(position).toHaveText('60, 180');
  await expect.poll(() => canvas.screenshot().then(bytes => bytes.length)).toBeGreaterThan(2000);
  const initial = await canvas.screenshot();
  await page.screenshot({ path: testInfo.outputPath('initial.png') });
  for (let run = 0; run < 2; run++) {
    await canvas.focus();
    await page.keyboard.down('ArrowRight');
    await expect(score).toHaveText('3 / 3');
    await page.keyboard.up('ArrowRight');
    await expect(position).not.toHaveText('60, 180');
    expect((await canvas.screenshot()).equals(initial)).toBe(false);
    await page.screenshot({ path: testInfo.outputPath(`collected-${run}.png`) });
    await page.getByRole('button', { name: 'Reset game' }).click();
    await expect(score).toHaveText('0 / 3');
    await expect(position).toHaveText('60, 180');
  }
  // Pointer movement exercises the canvas coordinate conversion, not a state hook.
  const box = await canvas.boundingBox();
  if (!box) throw new Error('Canvas has no bounds');
  await canvas.click({ position: { x: box.width * 0.3, y: box.height * 0.5 } });
  await expect(score).toHaveText('1 / 3');
  await page.getByRole('button', { name: 'Reset game' }).click();
  await canvas.focus();
  await page.keyboard.down('ArrowRight');
  await expect(position).not.toHaveText('60, 180');
  // Focus leaves the canvas while the key is physically held.
  await page.getByRole('button', { name: 'Reset game' }).focus();
  const stopped = await position.textContent();
  await page.waitForTimeout(300);
  expect(await position.textContent()).toBe(stopped);
  await page.keyboard.up('ArrowRight');
  await page.setViewportSize({ width: 420, height: 760 });
  await expect.poll(async () => (await canvas.boundingBox())!.width).toBeLessThan(box.width);
  await expect(canvas).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('narrow.png') });
  // Verify a real WebGL2 renderer for Three, not a mock or a DOM-only substitute.
  if (await page.locator('body').getAttribute('data-engine') === 'threejs') {
    const version = await canvas.evaluate(element => {
      const gl = (element as HTMLCanvasElement).getContext('webgl2');
      if (!gl) throw new Error('No actual WebGL2 context');
      return gl.getParameter(gl.VERSION) as string;
    });
    expect(version).toContain('WebGL 2.0');
  }
  expect(errors).toEqual([]);
});


test('pagehide releases the canvas and keyboard listeners', async ({ page }) => {
  await page.addInitScript(() => {
    const active = new Set<EventListenerOrEventListenerObject>();
    const add = window.addEventListener.bind(window);
    const remove = window.removeEventListener.bind(window);
    window.addEventListener = ((type: string, listener: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions) => {
      if (type === 'keydown') active.add(listener);
      add(type, listener, options);
    }) as typeof window.addEventListener;
    window.removeEventListener = ((type: string, listener: EventListenerOrEventListenerObject, options?: boolean | EventListenerOptions) => {
      if (type === 'keydown') active.delete(listener);
      remove(type, listener, options);
    }) as typeof window.removeEventListener;
    Object.defineProperty(window, '__activeKeydownListeners', { get: () => active.size });
  });
  await page.goto('/');
  await expect(page.locator('#game canvas')).toBeVisible();
  await expect.poll(() => page.evaluate(() => Reflect.get(window, '__activeKeydownListeners'))).toBeGreaterThan(0);
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pagehide')));
  await expect(page.locator('#game canvas')).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => Reflect.get(window, '__activeKeydownListeners'))).toBe(0);
});


test('WASD starts and stops across actual modifier changes', async ({ page }) => {
  await page.goto('/');
  const canvas = page.locator('#game canvas');
  const position = page.locator('#position');
  await canvas.focus();
  await page.keyboard.down('d');
  await expect(position).not.toHaveText('60, 180');
  await page.keyboard.down('Shift');
  await page.keyboard.up('D');
  await page.keyboard.up('Shift');
  const stopped = await position.textContent();
  await page.waitForTimeout(300);
  expect(await position.textContent()).toBe(stopped);
  await page.keyboard.down('Shift');
  await page.keyboard.down('W');
  await expect(position).not.toHaveText(stopped!);
  await page.keyboard.up('Shift');
  await page.keyboard.up('w');
  const stoppedAgain = await position.textContent();
  await page.waitForTimeout(300);
  expect(await position.textContent()).toBe(stoppedAgain);
});

test('persisted hide/show retains the game and restores input without held movement', async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto('/');
  const canvas = page.locator('#game canvas');
  const position = page.locator('#position');
  await canvas.focus();
  await page.keyboard.down('ArrowRight');
  await expect(position).not.toHaveText('60, 180');
  // Exercise the persisted browser lifecycle event contract explicitly. This does
  // not claim that the browser's independent BFCache eligibility decision ran.
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true })));
  await page.keyboard.up('ArrowRight');
  const suspended = await position.textContent();
  await expect(canvas).toHaveCount(1);
  await page.waitForTimeout(300);
  expect(await position.textContent()).toBe(suspended);
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
  await expect(canvas).toBeVisible();
  await page.waitForTimeout(300);
  expect(await position.textContent()).toBe(suspended);
  await canvas.focus();
  await page.keyboard.down('ArrowRight');
  await expect(page.locator('#score')).toHaveText('3 / 3');
  await page.keyboard.up('ArrowRight');
  await page.screenshot({ path: testInfo.outputPath('restored.png') });
  await page.getByRole('button', { name: 'Reset game' }).click();
  await expect(position).toHaveText('60, 180');
  expect(errors).toEqual([]);
});

import { afterEach, describe, expect, it, vi } from 'vitest';
import { bindInput } from '../../src/gameplay/input';

// Minimal DOM boundary; the real input module owns all key state and handlers.
function inputFixture() {
  const target = new EventTarget();
  const canvas = Object.assign(new EventTarget(), { setAttribute() {}, tabIndex: -1 });
  const document = Object.assign(new EventTarget(), { activeElement: canvas, hidden: false });
  vi.stubGlobal('window', target); vi.stubGlobal('document', document);
  const config = { width: 600, height: 360, radius: 12, speed: 120, tick: 1 / 60,
    start: { x: 60, y: 180 }, pickupRadius: 16, pickups: [] };
  const controls = bindInput(canvas as unknown as HTMLCanvasElement, config);
  const state = { x: 60, y: 180, score: 0, collected: [] };
  function key(type: string, key: string) { target.dispatchEvent(Object.assign(new Event(type), { key })); }
  return { key, controls, sample: () => ({ ...controls.sample(state, config.tick) }) };
}

afterEach(() => vi.unstubAllGlobals());
describe('movement key modifiers', () => {
  it('releases movement when Shift changes the release character', () => {
    const input = inputFixture();
    try {
      input.key('keydown', 'd'); input.key('keydown', 'Shift');
      expect(input.sample()).toEqual({ x: 1, y: 0 });
      input.key('keyup', 'D'); input.key('keyup', 'Shift');
      expect(input.sample()).toEqual({ x: 0, y: 0 });
    } finally { input.controls.dispose(); }
  });
  it('accepts uppercase WASD and releases it after modifiers change', () => {
    const input = inputFixture();
    try {
      input.key('keydown', 'W'); input.key('keydown', 'D');
      expect(input.sample()).toEqual({ x: 1, y: -1 });
      input.key('keyup', 'w'); input.key('keyup', 'd');
      expect(input.sample()).toEqual({ x: 0, y: 0 });
    } finally { input.controls.dispose(); }
  });
});

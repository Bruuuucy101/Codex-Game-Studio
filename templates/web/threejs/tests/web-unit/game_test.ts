import { describe, expect, it } from 'vitest';
import { createGame } from '../../src/gameplay/game';
import { FixedStep } from '../../src/core/step';

const config = { width: 600, height: 360, radius: 12, speed: 120, tick: 1 / 60,
  start: { x: 60, y: 180 }, pickupRadius: 16,
  pickups: [{ x: 180, y: 180 }, { x: 300, y: 180 }] };

describe('collect simulation', () => {
  it('moves at normalized speed on a diagonal', () => {
    const game = createGame(config);
    game.step(1, 1, 1);
    expect(Math.hypot(game.state.x - 60, game.state.y - 180)).toBeCloseTo(120);
  });
  it('clamps the player at all world bounds', () => {
    const game = createGame(config);
    game.step(-1, -1, 100);
    expect([game.state.x, game.state.y]).toEqual([12, 12]);
    game.step(1, 1, 100);
    expect([game.state.x, game.state.y]).toEqual([588, 348]);
  });
  it('collects each token once and resets independent state twice', () => {
    const game = createGame(config);
    const other = createGame(config);
    for (let run = 0; run < 2; run++) {
      for (let n = 0; n < 60; n++) game.step(1, 0, config.tick);
      expect(game.state.score).toBe(1);
      game.step(0, 0, 1);
      expect(game.state.score).toBe(1);
      for (let n = 0; n < 60; n++) game.step(1, 0, config.tick);
      expect(game.state.score).toBe(2);
      game.reset();
      expect(game.state).toEqual({ x: 60, y: 180, score: 0, collected: [false, false] });
    }
    expect(other.state.score).toBe(0);
    expect(config.pickups[0]).toEqual({ x: 180, y: 180 });
  });
  it('fixed stepping is deterministic across render frame partitions', () => {
    const a = createGame(config), b = createGame(config);
    const one = new FixedStep(config.tick), two = new FixedStep(config.tick);
    for (let n = 0; n < 120; n++) one.advance(1 / 120, dt => a.step(1, 0, dt));
    for (let n = 0; n < 20; n++) two.advance(1 / 20, dt => b.step(1, 0, dt));
    expect(a.state).toEqual(b.state);
    expect(a.state.x).toBeCloseTo(180);
  });
  it('reset clears the fixed-step remainder; invalid elapsed time is ignored', () => {
    const clock = new FixedStep(0.1);
    let ticks = 0;
    clock.advance(0.09, () => ticks++);
    clock.reset();
    clock.advance(-1, () => ticks++);
    clock.advance(Number.NaN, () => ticks++);
    clock.advance(0.02, () => ticks++);
    expect(ticks).toBe(0);
    clock.advance(0.08, () => ticks++);
    expect(ticks).toBe(1);
  });
});

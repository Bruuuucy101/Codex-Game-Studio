/** Implements the Signal Field collect/reset design in README-WEB.md. */
export interface Point { x: number; y: number }
export interface GameConfig {
  width: number; height: number; radius: number; speed: number; tick: number;
  start: Point; pickupRadius: number; pickups: Point[];
}
export interface GameState extends Point { score: number; collected: boolean[] }

/** Pure single-thread simulation. Example: const game = createGame(config); game.step(1, 0, config.tick). */
export function createGame(config: GameConfig) {
  const state: GameState = { ...config.start, score: 0, collected: config.pickups.map(() => false) };
  function reset(): void {
    state.x = config.start.x; state.y = config.start.y; state.score = 0;
    state.collected.fill(false);
  }
  function step(x: number, y: number, dt: number): void {
    const length = Math.hypot(x, y);
    const scale = length > 1 ? 1 / length : 1;
    state.x = Math.max(config.radius, Math.min(config.width - config.radius, state.x + x * scale * config.speed * dt));
    state.y = Math.max(config.radius, Math.min(config.height - config.radius, state.y + y * scale * config.speed * dt));
    for (let i = 0; i < config.pickups.length; i++) {
      const pickup = config.pickups[i];
      if (!state.collected[i] && Math.hypot(state.x - pickup.x, state.y - pickup.y) <= config.radius + config.pickupRadius) {
        state.collected[i] = true;
        state.score++;
      }
    }
  }
  return { state, step, reset };
}

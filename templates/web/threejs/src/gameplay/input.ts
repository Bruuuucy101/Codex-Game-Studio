import type { GameConfig, GameState } from './game';

/** Owns DOM input listeners; call dispose on engine shutdown. */
export function bindInput(canvas: HTMLCanvasElement, config: GameConfig) {
  const keys = new Set<string>();
  const direction = { x: 0, y: 0 };
  let target: { x: number; y: number } | null = null;
  const movement = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a', 's', 'd']);
  canvas.tabIndex = 0;
  canvas.setAttribute('aria-label', 'Game field: arrow keys or WASD to move');
  function clear(): void { keys.clear(); target = null; direction.x = 0; direction.y = 0; }
  function down(event: KeyboardEvent): void {
    if (document.activeElement !== canvas || !movement.has(event.key)) return;
    event.preventDefault(); keys.add(event.key); target = null;
  }
  function up(event: KeyboardEvent): void { keys.delete(event.key); }
  function pointer(event: PointerEvent): void {
    canvas.focus();
    const rect = canvas.getBoundingClientRect();
    target = { x: (event.clientX - rect.left) * config.width / rect.width,
      y: (event.clientY - rect.top) * config.height / rect.height };
  }
  function visibility(): void { if (document.hidden) clear(); }
  window.addEventListener('keydown', down);
  window.addEventListener('keyup', up);
  window.addEventListener('blur', clear);
  document.addEventListener('visibilitychange', visibility);
  canvas.addEventListener('blur', clear);
  canvas.addEventListener('pointerdown', pointer);
  return {
    clear,
    sample(state: GameState, dt: number) {
      direction.x = Number(keys.has('ArrowRight') || keys.has('d')) - Number(keys.has('ArrowLeft') || keys.has('a'));
      direction.y = Number(keys.has('ArrowDown') || keys.has('s')) - Number(keys.has('ArrowUp') || keys.has('w'));
      if (target) {
        const x = target.x - state.x, y = target.y - state.y;
        const distance = Math.hypot(x, y);
        if (distance < 0.01) target = null;
        else {
          const divisor = Math.max(distance, config.speed * dt);
          direction.x = x / divisor; direction.y = y / divisor;
        }
      }
      return direction;
    },
    dispose() {
      clear();
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', clear);
      document.removeEventListener('visibilitychange', visibility);
      canvas.removeEventListener('blur', clear);
      canvas.removeEventListener('pointerdown', pointer);
    },
  };
}

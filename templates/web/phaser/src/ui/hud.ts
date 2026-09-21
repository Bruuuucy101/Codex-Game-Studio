import type { GameState } from '../gameplay/game';

/** DOM view only; reset requests go back to the scene owner. */
export function bindHud(total: number, reset: () => void) {
  const score = document.querySelector<HTMLElement>('#score')!;
  const position = document.querySelector<HTMLElement>('#position')!;
  const status = document.querySelector<HTMLElement>('#status')!;
  const button = document.querySelector<HTMLButtonElement>('#reset')!;
  button.addEventListener('click', reset);
  return {
    render(state: GameState) {
      const scoreText = `${state.score} / ${total}`;
      if (score.textContent !== scoreText) score.textContent = scoreText;
      const pointText = `${Math.round(state.x)}, ${Math.round(state.y)}`;
      if (position.textContent !== pointText) position.textContent = pointText;
      const message = state.score === total ? 'All signals collected. Nicely done!' : 'Ready to explore';
      if (status.textContent !== message) status.textContent = message;
    },
    dispose() { button.removeEventListener('click', reset); },
  };
}

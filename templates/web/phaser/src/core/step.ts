/** Fixed simulation clock, independent of the engine. Example: clock.advance(dt, step). */
export class FixedStep {
  private remainder = 0;
  constructor(private readonly tick: number) {}
  advance(elapsed: number, step: (dt: number) => void): void {
    if (!Number.isFinite(elapsed) || elapsed <= 0) return;
    // Bound catch-up after suspension; never simulate an entire hidden-tab interval.
    this.remainder += Math.min(elapsed, 0.25);
    while (this.remainder + 1e-12 >= this.tick) {
      step(this.tick);
      this.remainder = Math.max(0, this.remainder - this.tick);
    }
  }
  reset(): void { this.remainder = 0; }
}

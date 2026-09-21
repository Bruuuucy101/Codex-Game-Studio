import Phaser from 'phaser';
import config from '../../assets/data/game.json';
import { FixedStep } from '../core/step';
import { createGame } from '../gameplay/game';
import { bindInput } from '../gameplay/input';
import { bindHud } from '../ui/hud';

/** Phaser owns scene objects; this scene owns its DOM listeners and simulation. */
export class CollectScene extends Phaser.Scene {
  private simulation = createGame(config);
  private clock = new FixedStep(config.tick);
  private controls?: ReturnType<typeof bindInput>;
  private hud?: ReturnType<typeof bindHud>;
  private player?: Phaser.GameObjects.Arc;
  private pickups: Phaser.GameObjects.Rectangle[] = [];
  constructor() { super('collect'); }
  create(): void {
    this.simulation.reset(); this.clock.reset();
    const grid = this.add.graphics().lineStyle(1, 0x27434e, 0.7);
    for (let x = 0; x <= config.width; x += 30) grid.lineBetween(x, 0, x, config.height);
    for (let y = 0; y <= config.height; y += 30) grid.lineBetween(0, y, config.width, y);
    this.pickups = config.pickups.map(point => this.add.rectangle(point.x, point.y,
      config.pickupRadius * 1.4, config.pickupRadius * 1.4, 0xf8ca6a).setAngle(45));
    this.player = this.add.circle(config.start.x, config.start.y, config.radius, 0x8ee2d2).setStrokeStyle(3, 0xe5fffa);
    this.controls = bindInput(this.game.canvas, config);
    this.hud = bindHud(config.pickups.length, () => {
      this.simulation.reset(); this.clock.reset(); this.controls?.clear(); this.renderState();
    });
    const cleanup = (): void => {
      this.events.off(Phaser.Scenes.Events.SHUTDOWN, cleanup);
      this.events.off(Phaser.Scenes.Events.DESTROY, cleanup);
      this.controls?.dispose(); this.hud?.dispose();
      this.controls = undefined; this.hud = undefined; this.pickups = [];
    };
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, cleanup);
    this.events.once(Phaser.Scenes.Events.DESTROY, cleanup);
    this.renderState();
  }
  private simulate = (dt: number): void => {
    const direction = this.controls!.sample(this.simulation.state, dt);
    this.simulation.step(direction.x, direction.y, dt);
  };
  private renderState(): void {
    const state = this.simulation.state;
    this.player?.setPosition(state.x, state.y);
    for (let i = 0; i < this.pickups.length; i++) this.pickups[i].setVisible(!state.collected[i]);
    this.hud?.render(state);
  }
  update(_time: number, delta: number): void {
    this.clock.advance(delta / 1000, this.simulate);
    this.renderState();
  }
}

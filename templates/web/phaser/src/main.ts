import Phaser from 'phaser';
import config from '../assets/data/game.json';
import { CollectScene } from './scenes/collect';
import { bindPageLifecycle } from './core/page-lifecycle';
import './styles.css';

const game = new Phaser.Game({
  type: Phaser.AUTO, parent: 'game', width: config.width, height: config.height,
  backgroundColor: '#182c36', scene: CollectScene,
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  audio: { noAudio: true }, banner: false,
});
const dispose = bindPageLifecycle(window, {
  suspend() { game.canvas.blur(); game.loop.sleep(); },
  resume() { game.loop.resetDelta(); game.loop.wake(); },
  dispose() {
    game.destroy(true);
    // Destruction is queued for a frame; wake a suspended loop to complete it.
    game.loop.wake();
  },
});
if (import.meta.hot) import.meta.hot.dispose(dispose);

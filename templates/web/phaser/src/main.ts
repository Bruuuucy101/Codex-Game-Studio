import Phaser from 'phaser';
import config from '../assets/data/game.json';
import { CollectScene } from './scenes/collect';
import './styles.css';

const game = new Phaser.Game({
  type: Phaser.AUTO, parent: 'game', width: config.width, height: config.height,
  backgroundColor: '#182c36', scene: CollectScene,
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  audio: { noAudio: true }, banner: false,
});
let disposed = false;
function dispose(): void {
  if (disposed) return;
  disposed = true;
  window.removeEventListener('pagehide', dispose);
  game.destroy(true);
}
window.addEventListener('pagehide', dispose);
if (import.meta.hot) import.meta.hot.dispose(dispose);

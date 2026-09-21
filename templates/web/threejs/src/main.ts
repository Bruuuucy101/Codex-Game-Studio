import { startCollect } from './scenes/collect';
import './styles.css';

const stop = startCollect(document.querySelector<HTMLElement>('#game')!);
function dispose(): void { window.removeEventListener('pagehide', dispose); stop(); }
window.addEventListener('pagehide', dispose);
if (import.meta.hot) import.meta.hot.dispose(dispose);

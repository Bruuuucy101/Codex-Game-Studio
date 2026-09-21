import { startCollect } from './scenes/collect';
import { bindPageLifecycle } from './core/page-lifecycle';
import './styles.css';

const dispose = bindPageLifecycle(window, startCollect(document.querySelector<HTMLElement>('#game')!));
if (import.meta.hot) import.meta.hot.dispose(dispose);

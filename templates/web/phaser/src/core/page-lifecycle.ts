/** The page owns final disposal; back/forward-cache transitions only suspend it. */
export interface PageOwner { suspend(): void; resume(): void; dispose(): void }

/** Example: bindPageLifecycle(window, sceneOwner); returned disposer also owns HMR cleanup. */
export function bindPageLifecycle(target: EventTarget, owner: PageOwner): () => void {
  let state: 'live' | 'suspended' | 'disposed' = 'live';
  function dispose(): void {
    if (state === 'disposed') return;
    state = 'disposed';
    target.removeEventListener('pagehide', hide);
    target.removeEventListener('pageshow', show);
    owner.dispose();
  }
  function hide(event: Event): void {
    if (!(event as PageTransitionEvent).persisted) { dispose(); return; }
    if (state === 'live') { state = 'suspended'; owner.suspend(); }
  }
  function show(event: Event): void {
    if ((event as PageTransitionEvent).persisted && state === 'suspended') {
      state = 'live'; owner.resume();
    }
  }
  target.addEventListener('pagehide', hide);
  target.addEventListener('pageshow', show);
  return dispose;
}

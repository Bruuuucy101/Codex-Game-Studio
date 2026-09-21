import { describe, expect, it } from 'vitest';
import { bindPageLifecycle } from '../../src/core/page-lifecycle';

function fixture() {
  const target = new EventTarget();
  const calls: string[] = [];
  const dispose = bindPageLifecycle(target, {
    suspend: () => calls.push('suspend'), resume: () => calls.push('resume'),
    dispose: () => calls.push('dispose'),
  });
  const send = (type: string, persisted: boolean) =>
    target.dispatchEvent(Object.assign(new Event(type), { persisted }));
  return { calls, dispose, send };
}

describe('page lifecycle ownership', () => {
  it('suspends and restores persisted pages repeatedly without destroying them', () => {
    const app = fixture();
    app.send('pageshow', false);
    for (let n = 0; n < 2; n++) {
      app.send('pagehide', true); app.send('pagehide', true);
      app.send('pageshow', true); app.send('pageshow', true);
    }
    expect(app.calls).toEqual(['suspend', 'resume', 'suspend', 'resume']);
    app.dispose();
  });
  it('finally disposes once and removes listeners, including while suspended', () => {
    const app = fixture();
    app.send('pagehide', true);
    app.send('pagehide', false);
    app.send('pageshow', true); app.send('pagehide', false); app.dispose();
    expect(app.calls).toEqual(['suspend', 'dispose']);
  });
  it('HMR disposal removes the live page listeners', () => {
    const app = fixture();
    app.dispose(); app.send('pagehide', true); app.send('pageshow', true);
    expect(app.calls).toEqual(['dispose']);
  });
});

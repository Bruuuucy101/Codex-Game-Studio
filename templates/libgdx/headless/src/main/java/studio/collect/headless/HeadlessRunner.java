package studio.collect.headless;

import com.badlogic.gdx.*;
import com.badlogic.gdx.backends.headless.HeadlessApplication;
import com.badlogic.gdx.backends.headless.HeadlessApplicationConfiguration;
import java.util.concurrent.TimeoutException;

/** Bounded real-backend runner. Callbacks must not block; one Gdx application at a time. */
public final class HeadlessRunner {
    private HeadlessRunner() { }

    public static synchronized void run(ApplicationListener listener, long timeoutMillis) throws Exception {
        if (timeoutMillis <= 0) throw new IllegalArgumentException("Timeout must be positive");
        Application oldApp = Gdx.app; Graphics oldGraphics = Gdx.graphics;
        Audio oldAudio = Gdx.audio; Input oldInput = Gdx.input;
        Files oldFiles = Gdx.files; Net oldNet = Gdx.net;
        Guard guard = new Guard(listener);
        ManagedApplication app = null;
        try {
            HeadlessApplicationConfiguration config = new HeadlessApplicationConfiguration();
            config.updatesPerSecond = 240;
            app = new ManagedApplication(guard, config);
            if (!app.await(timeoutMillis)) throw new TimeoutException("Headless lifecycle exceeded " + timeoutMillis + "ms");
            guard.rethrow();
        } finally {
            if (app != null && app.alive()) {
                app.exit();
                if (!app.await(2000)) {
                    // Never use Thread.stop or restore globals under a still-running callback.
                    throw new IllegalStateException("Headless callback did not stop; callbacks must not block");
                }
            }
            Gdx.app = oldApp; Gdx.graphics = oldGraphics; Gdx.audio = oldAudio;
            Gdx.input = oldInput; Gdx.files = oldFiles; Gdx.net = oldNet;
            // The headless backend never sets GL fields; leave preexisting GL state untouched.
        }
    }
    private static final class ManagedApplication extends HeadlessApplication {
        ManagedApplication(Guard guard, HeadlessApplicationConfiguration config) { super(guard, config); }
        @Override protected void mainLoop() {
            // listener is initialized before super starts the thread; no subclass-init race.
            Guard guard = (Guard) listener;
            try { super.mainLoop(); }
            catch (Throwable failure) { guard.fail(failure); }
            finally { guard.close(); }
        }
        boolean alive() { return mainLoopThread.isAlive(); }
        boolean await(long millis) throws InterruptedException {
            mainLoopThread.join(millis);
            return !alive();
        }
    }
    private static final class Guard implements ApplicationListener {
        final ApplicationListener target;
        Throwable failure;
        boolean paused, disposed;
        Guard(ApplicationListener target) { this.target = target; }
        void fail(Throwable next) {
            if (failure == null) failure = next;
            else if (failure != next) failure.addSuppressed(next);
        }
        void rethrow() throws Exception {
            if (failure instanceof Error) throw (Error) failure;
            if (failure instanceof Exception) throw (Exception) failure;
            if (failure != null) throw new RuntimeException(failure);
        }
        public void create() { target.create(); }
        public void resize(int w, int h) { target.resize(w, h); }
        public void render() { target.render(); }
        public void resume() { target.resume(); }
        public void pause() { if (!paused) { paused = true; target.pause(); } }
        public void dispose() { if (!disposed) { disposed = true; target.dispose(); } }
        void close() {
            try { pause(); } catch (Throwable next) { fail(next); }
            try { dispose(); } catch (Throwable next) { fail(next); }
        }
    }
}

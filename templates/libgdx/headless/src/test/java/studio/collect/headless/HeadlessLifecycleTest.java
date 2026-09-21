package studio.collect.headless;

import com.badlogic.gdx.ApplicationAdapter;
import com.badlogic.gdx.Application;
import com.badlogic.gdx.Gdx;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import studio.collect.gameplay.CollectGame;
import static org.junit.jupiter.api.Assertions.*;

@Timeout(15)
class HeadlessLifecycleTest {
    @Test void test_real_backend_collect_reset_pause_dispose_and_repeat_isolation() throws Exception {
        Application previous = Gdx.app;
        for (int repeat = 0; repeat < 2; repeat++) {
            ScriptedCollect application = new ScriptedCollect();
            HeadlessRunner.run(application, 5000);
            assertEquals(1, application.created);
            assertEquals(1, application.paused);
            assertEquals(1, application.disposed);
            assertEquals(1, application.collected);
            assertEquals(0, application.game.state().score());
            assertEquals(application.game.config().startX, application.game.state().x());
            assertSame(previous, Gdx.app);
        }
    }
    @Test void test_background_callback_failure_propagates_and_disposes() {
        int[] disposed = {0};
        ApplicationAdapter broken = new ApplicationAdapter() {
            @Override public void create() { throw new IllegalStateException("intentional create failure"); }
            @Override public void dispose() { disposed[0]++; }
        };
        IllegalStateException failure = assertThrows(IllegalStateException.class, () -> HeadlessRunner.run(broken, 2000));
        assertEquals("intentional create failure", failure.getMessage());
        assertEquals(1, disposed[0]);
        assertNull(Gdx.app);
    }
    @Test void test_never_exiting_listener_times_out_and_shuts_down() {
        int[] disposed = {0};
        ApplicationAdapter neverExits = new ApplicationAdapter() {
            @Override public void dispose() { disposed[0]++; }
        };
        assertThrows(java.util.concurrent.TimeoutException.class, () -> HeadlessRunner.run(neverExits, 100));
        assertEquals(1, disposed[0]);
        assertNull(Gdx.app);
    }
    private static class ScriptedCollect extends ApplicationAdapter {
        final CollectGame game = new CollectGame(CollectGame.NO_PRESENTATION);
        int created, paused, disposed, ticks, collected;
        boolean finished;
        @Override public void create() {
            assertEquals(Application.ApplicationType.HeadlessDesktop, Gdx.app.getType());
            assertNull(Gdx.gl);
            game.create();
            created++;
        }
        @Override public void render() {
            if (finished) return;
            if (ticks++ < 80) {
                game.advance(1, 0, false, game.config().fixedStep);
                game.render();
            } else {
                finished = true;
                collected = game.state().score();
                game.advance(0, 0, true, 0);
                Gdx.app.exit();
            }
        }
        @Override public void pause() { paused++; game.pause(); }
        @Override public void dispose() { disposed++; game.dispose(); }
    }
}

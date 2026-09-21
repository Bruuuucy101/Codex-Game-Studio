package studio.collect.headless;

import com.badlogic.gdx.ApplicationAdapter;
import com.badlogic.gdx.Gdx;
import studio.collect.gameplay.CollectGame;

/** Run a finite scripted collect round using the actual headless lifecycle. */
public final class HeadlessLauncher {
    public static void main(String[] args) throws Exception {
        CollectGame game = new CollectGame(CollectGame.NO_PRESENTATION);
        HeadlessRunner.run(new ApplicationAdapter() {
            boolean finished;
            @Override public void create() { game.create(); }
            @Override public void render() {
                if (finished) return;
                game.advance(1, 0, false, game.config().fixedStep);
                game.render();
                if (game.state().won()) {
                    System.out.println("Collected signal; score=" + game.state().score());
                    finished = true;
                    Gdx.app.exit();
                }
            }
            @Override public void pause() { game.pause(); }
            @Override public void dispose() { game.dispose(); }
        }, 5000);
    }
}

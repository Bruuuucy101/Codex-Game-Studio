package studio.collect.desktop;

import com.badlogic.gdx.*;
import com.badlogic.gdx.backends.lwjgl3.*;
import com.badlogic.gdx.graphics.GL20;
import com.badlogic.gdx.graphics.OrthographicCamera;
import com.badlogic.gdx.graphics.g2d.BitmapFont;
import com.badlogic.gdx.graphics.g2d.SpriteBatch;
import com.badlogic.gdx.graphics.glutils.ShapeRenderer;
import com.badlogic.gdx.utils.I18NBundle;
import com.badlogic.gdx.utils.viewport.FitViewport;
import studio.collect.gameplay.*;

/** Desktop-only input/rendering. Run via :lwjgl3:run; see macOS first-thread note. */
public final class DesktopLauncher {
    public static void main(String[] args) {
        Lwjgl3ApplicationConfiguration window = new Lwjgl3ApplicationConfiguration();
        window.setTitle("CCGS libGDX collect");
        window.setWindowedMode(960, 540);
        window.useVsync(true);
        new Lwjgl3Application(new ApplicationAdapter() {
            final CollectGame game = new CollectGame(new DesktopPresentation());
            @Override public void create() { game.create(); }
            @Override public void render() {
                float x = axis(Input.Keys.D, Input.Keys.RIGHT) - axis(Input.Keys.A, Input.Keys.LEFT);
                float y = axis(Input.Keys.W, Input.Keys.UP) - axis(Input.Keys.S, Input.Keys.DOWN);
                game.advance(x, y, Gdx.input.isKeyJustPressed(Input.Keys.R), Gdx.graphics.getDeltaTime());
                game.render();
            }
            private int axis(int first, int second) {
                return Gdx.input.isKeyPressed(first) || Gdx.input.isKeyPressed(second) ? 1 : 0;
            }
            @Override public void resize(int w, int h) { game.resize(w, h); }
            @Override public void pause() { game.pause(); }
            @Override public void resume() { game.resume(); }
            @Override public void dispose() { game.dispose(); }
        }, window);
    }
    private static final class DesktopPresentation implements CollectGame.Presentation {
        GameConfig config;
        ShapeRenderer shapes;
        SpriteBatch batch;
        BitmapFont font;
        FitViewport viewport;
        I18NBundle text;
        public void create(GameConfig config) {
            this.config = config;
            viewport = new FitViewport(config.width, config.height, new OrthographicCamera());
            text = I18NBundle.createBundle(Gdx.files.internal("i18n/messages"));
            shapes = new ShapeRenderer();
            batch = new SpriteBatch();
            font = new BitmapFont();
            font.getData().setScale(.65f);
        }
        public void draw(CollectState state) {
            Gdx.gl.glClearColor(.035f, .055f, .10f, 1);
            Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT);
            viewport.apply();
            shapes.setProjectionMatrix(viewport.getCamera().combined);
            shapes.begin(ShapeRenderer.ShapeType.Filled);
            if (!state.won()) {
                shapes.setColor(1, .70f, .20f, 1);
                shapes.circle(config.targetX, config.targetY, config.targetRadius);
            }
            shapes.setColor(.25f, .85f, 1, 1);
            shapes.rect(state.x() - config.playerRadius, state.y() - config.playerRadius,
                        config.playerRadius * 2, config.playerRadius * 2);
            shapes.end();
            batch.setProjectionMatrix(viewport.getCamera().combined);
            batch.begin();
            font.draw(batch, text.get("title"), 8, config.height - 8);
            font.draw(batch, text.format("score", state.score()), 8, config.height - 24);
            font.draw(batch, text.get(state.won() ? "won" : "controls"), 8, 16);
            batch.end();
        }
        public void resize(int width, int height) { if (viewport != null) viewport.update(width, height, true); }
        public void pause() { /* Input is polled per frame; no held command cache survives pause. */ }
        public void dispose() {
            if (shapes != null) { shapes.dispose(); shapes = null; }
            if (batch != null) { batch.dispose(); batch = null; }
            if (font != null) { font.dispose(); font = null; }
        }
    }
}

package studio.collect.gameplay;

import com.badlogic.gdx.Game;
import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.ScreenAdapter;

/** Screen owner for the collect prototype; data is the sole balance source. */
public final class CollectGame extends Game {
    public interface Presentation {
        void create(GameConfig config);
        void draw(CollectState state);
        void resize(int width, int height);
        void pause();
        void dispose();
    }
    /** Headless production mode deliberately creates no GPU/audio objects. */
    public static final Presentation NO_PRESENTATION = new Presentation() {
        public void create(GameConfig config) { }
        public void draw(CollectState state) { }
        public void resize(int width, int height) { }
        public void pause() { }
        public void dispose() { }
    };
    private final Presentation presentation;
    private GameConfig config;
    private CollectState state;
    private boolean disposed;

    public CollectGame(Presentation presentation) { this.presentation = presentation; }
    public GameConfig config() { return config; }
    public CollectState state() { return state; }
    @Override public void create() {
        config = GameConfig.parse(Gdx.files.internal("data/game_config.json").readString("UTF-8"));
        state = new CollectState(config);
        // Assign the owned screen before initialization so partial creation can be disposed.
        screen = new ScreenAdapter() {
            @Override public void render(float delta) { presentation.draw(state); }
            @Override public void resize(int width, int height) { presentation.resize(width, height); }
            @Override public void pause() { presentation.pause(); }
            @Override public void dispose() { presentation.dispose(); }
        };
        presentation.create(config);
        screen.show();
        screen.resize(Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
    }
    /** Backend supplies controls/time; resets do not also move in the same command. */
    public void advance(float x, float y, boolean reset, float seconds) {
        if (!Float.isFinite(seconds) || seconds < 0) throw new IllegalArgumentException("Invalid frame time");
        if (reset) state.reset();
        else state.step(x, y, Math.min(seconds, config.maxDelta));
    }
    @Override public void dispose() {
        if (disposed) return;
        disposed = true;
        super.dispose(); // Game hides the screen; this owner must also dispose it.
        if (screen != null) screen.dispose();
    }
}

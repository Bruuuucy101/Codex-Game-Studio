package studio.collect.gameplay;

/** Pure collect-loop simulation. No Gdx/global state, rendering, clock or random input. */
public final class CollectState {
    private final GameConfig config;
    private float x, y;
    private int score;

    public CollectState(GameConfig config) { this.config = config; reset(); }
    public float x() { return x; }
    public float y() { return y; }
    public int score() { return score; }
    public boolean won() { return score == 1; }
    public void reset() { x = config.startX; y = config.startY; score = 0; }

    /** Advance injected input/time once; diagonal input is capped to unit magnitude. */
    public void step(float horizontal, float vertical, float seconds) {
        if (!Float.isFinite(seconds) || seconds < 0 || !Float.isFinite(horizontal)
                || !Float.isFinite(vertical)) throw new IllegalArgumentException("Input/time must be finite; time nonnegative");
        double length = Math.max(1, Math.hypot(horizontal, vertical));
        float oldX = x, oldY = y;
        x = (float) Math.max(config.playerRadius, Math.min(config.width - config.playerRadius,
                x + horizontal / length * config.speed * seconds));
        y = (float) Math.max(config.playerRadius, Math.min(config.height - config.playerRadius,
                y + vertical / length * config.speed * seconds));
        // Swept segment avoids skipping the signal on a long accepted step.
        double dx = x - oldX, dy = y - oldY;
        double squaredLength = dx * dx + dy * dy;
        double fraction = squaredLength == 0 ? 0 : Math.max(0, Math.min(1,
                ((config.targetX - oldX) * dx + (config.targetY - oldY) * dy) / squaredLength));
        double distance = Math.hypot(oldX + fraction * dx - config.targetX,
                                     oldY + fraction * dy - config.targetY);
        if (score == 0 && distance <= config.playerRadius + config.targetRadius) score = 1;
    }
}

package studio.collect.gameplay;

import com.badlogic.gdx.utils.JsonReader;
import com.badlogic.gdx.utils.JsonValue;

/** Immutable balance data from assets/data/game_config.json; see README-LIBGDX.md. */
public final class GameConfig {
    public final float width, height, playerRadius, targetRadius, speed;
    public final float startX, startY, targetX, targetY, fixedStep, maxDelta;

    private GameConfig(JsonValue data) {
        width = positive(data, "width"); height = positive(data, "height");
        playerRadius = positive(data, "playerRadius"); targetRadius = positive(data, "targetRadius");
        speed = positive(data, "speed"); fixedStep = positive(data, "fixedStep");
        maxDelta = positive(data, "maxDelta");
        startX = finite(data, "startX"); startY = finite(data, "startY");
        targetX = finite(data, "targetX"); targetY = finite(data, "targetY");
        if (fixedStep > maxDelta || !inside(startX, startY, playerRadius)
                || !inside(targetX, targetY, targetRadius)) {
            throw new IllegalArgumentException("Invalid bounds or timestep in game_config.json");
        }
    }
    /** Parse and validate all required fields; malformed data fails before gameplay starts. */
    public static GameConfig parse(String text) {
        try { return new GameConfig(new JsonReader().parse(text)); }
        catch (RuntimeException failure) {
            throw new IllegalArgumentException("Invalid game_config.json", failure);
        }
    }
    private boolean inside(float x, float y, float radius) {
        return x >= radius && y >= radius && x <= width - radius && y <= height - radius;
    }
    private static float positive(JsonValue data, String name) {
        float value = finite(data, name);
        if (value <= 0) throw new IllegalArgumentException(name + " must be positive");
        return value;
    }
    private static float finite(JsonValue data, String name) {
        float value = data.getFloat(name);
        if (!Float.isFinite(value)) throw new IllegalArgumentException(name + " must be finite");
        return value;
    }
}

package studio.collect.gameplay;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CollectStateTest {
    private GameConfig config() {
        return GameConfig.parse("{\"width\":100,\"height\":100,\"playerRadius\":2,\"targetRadius\":2,\"speed\":10,\"startX\":10,\"startY\":10,\"targetX\":30,\"targetY\":10,\"fixedStep\":0.1,\"maxDelta\":0.25}");
    }
    @Test void test_movement_diagonal_has_same_speed() {
        CollectState state = new CollectState(config());
        state.step(1, 1, 1);
        assertEquals(10, Math.hypot(state.x() - 10, state.y() - 10), 0.0001);
    }
    @Test void test_movement_clamps_at_bounds() {
        CollectState state = new CollectState(config());
        state.step(-1, -1, 100);
        assertEquals(2, state.x());
        assertEquals(2, state.y());
        state.step(1, 1, 100);
        assertEquals(98, state.x());
        assertEquals(98, state.y());
    }
    @Test void test_collect_crossed_target_scores_once() {
        CollectState state = new CollectState(config());
        state.step(1, 0, 8);
        assertEquals(1, state.score());
        assertTrue(state.won());
        state.step(-1, 0, 8);
        assertEquals(1, state.score());
    }
    @Test void test_reset_restores_position_and_collectible() {
        CollectState state = new CollectState(config());
        state.step(1, 0, 2);
        state.reset();
        assertEquals(10, state.x());
        assertEquals(10, state.y());
        assertEquals(0, state.score());
        assertFalse(state.won());
        state.step(1, 0, 2);
        assertEquals(1, state.score());
    }
    @Test void test_step_rejects_invalid_time_and_input_without_mutation() {
        CollectState state = new CollectState(config());
        for (float dt : new float[]{-1, Float.NaN, Float.POSITIVE_INFINITY}) {
            assertThrows(IllegalArgumentException.class, () -> state.step(1, 0, dt));
        }
        assertThrows(IllegalArgumentException.class, () -> state.step(Float.NaN, 0, 1));
        assertEquals(10, state.x());
        assertEquals(0, state.score());
    }
    @Test void test_equal_fixed_steps_produce_equal_state() {
        CollectState first = new CollectState(config());
        CollectState second = new CollectState(config());
        for (int i = 0; i < 20; i++) { first.step(1, 0, .1f); second.step(1, 0, .1f); }
        assertEquals(first.x(), second.x());
        assertEquals(30, first.x(), .001);
        assertEquals(1, first.score());
    }
    @Test void test_config_missing_or_impossible_values_fail() {
        assertThrows(IllegalArgumentException.class, () -> GameConfig.parse("{}"));
        assertThrows(IllegalArgumentException.class, () -> GameConfig.parse("{broken"));
        String valid = "{\"width\":100,\"height\":100,\"playerRadius\":2,\"targetRadius\":2,\"speed\":10,\"startX\":10,\"startY\":10,\"targetX\":30,\"targetY\":10,\"fixedStep\":0.1,\"maxDelta\":0.25}";
        assertThrows(IllegalArgumentException.class, () -> GameConfig.parse(valid.replace("\"speed\":10", "\"speed\":-1")));
        assertThrows(IllegalArgumentException.class, () -> GameConfig.parse(valid.replace("\"startX\":10", "\"startX\":101")));
    }
}

# Screen Navigation - Reference

Explains configuration structure, runtime behavior, and timing controls for `ScreenNavigator` and `ScreenState`.

## Configuration

`config/screen_config.json` defines page targets. Loaded by `ScreenState` at startup. Only `enabled: true` screens are processed.

### Descriptor Fields

- `menu_location`: String identifier mapped to `ScreenNavigator.determine_button()`.
- `grid_type`: Category passed to matching routines (`Equipment`, `Items`, `Students`, `Student`, `currencies`).
- `uses_menu_tab`: `true` -> opens menu tab first. `false` -> navigates from Home.
- `enabled`: Toggles screen participation.

## Runtime Behavior (`ScreenState`)

1. Loads enabled screens into `screen_mapping`.
2. Checks current page via `navigator.identify_screen()`.
3. Ensures UI state (`ensure_at_home()` / `ensure_menu_state()`).
4. Calls `navigate_to_target()`, verifies result.
5. Executes processor:
   - `Currencies` -> `get_currencies()`
   - `Equipment`/`Items` -> `startMatching(...)`
   - `Students` -> chains to `Student` -> `get_student_info()`
6. Tracks `visited`/`unvisited` sets until completion.

## Timing & Tuning

Delays are scaled by values in `config/settings.json`:

- `wait_multiplier` (default `1.0`): Base action delay.
- `wait_screen_nav_multiplier` (default `2.0`): Screen transition delay.
- `capture_interval` (default `0.5`): Background screenshot thread frequency.

**Recommendation**: Keep `wait_multiplier` low for responsiveness. Raise `wait_screen_nav_multiplier` if page loads are inconsistent.

## Troubleshooting

- **Screen never detected**: Verify `menu_location` exists in `determine_button()`. Check OCR title output in logs.
- **Swipe/Navigation desync**: Increase `wait_screen_nav_multiplier`. Ensure `1280x720` resolution with no scaling.
- **Linux AMD GPU PNG corruption**: ADB `exec-out` stderr can corrupt bytes. The code already redirects stderr, but ensure your ADB version supports `exec-out`.

## Adding a New Screen

1. Add entry to `screen_config.json`.
2. Add `menu_location` mapping in `ScreenNavigator.determine_button()`.
3. If new `grid_type`, add processing call in `ScreenState._execute_process()`.
4. Test with `python launch.py`.

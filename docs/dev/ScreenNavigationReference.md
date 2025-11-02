# Screen Navigation - Reference

This document explains the screen navigation configuration and runtime behavior used by `ScreenNavigator` and `ScreenState`.

## Purpose

`screen_config.json` defines which in-game pages the scanner should visit and how to reach them. `ScreenState` reads this file to drive navigation, trigger matching/collection routines, and manage special-case flows (for example: `Students` -> `Student` details).

## Location

`config/screen_config.json` (example shipped at `config/screen_config.json`)

## Top-level structure

- `screens`: mapping of screen name -> screen descriptor

Example:

```json
{
  "screens": {
    "Currencies": {
      "menu_location": "currencies",
      "grid_type": "currencies",
      "uses_menu_tab": false,
      "enabled": true
    }
  }
}
```

## Descriptor fields

- `menu_location` (string)
  - Identifier used by `ScreenNavigator` to tap the UI control that opens the screen.
  - Must match a key/selector implemented in `ScreenNavigator` (examples: `menu_items`, `menu_equipment`, `currencies`, `first_student`).
- `grid_type` (string)
  - Logical category for downstream processors (used by matching routines). Examples: `Equipment`, `Items`, `Students`, `Student`, `currencies`.
- `uses_menu_tab` (bool)
  - `true`: open the menu tab and select the item inside the tab.
  - `false`: navigation is performed from the Home UI (the scanner will call `navigator.go_home()` first when needed).
- `enabled` (bool)
  - When `false` the entry is ignored by `ScreenState`.

## Runtime behavior (ScreenState)

- On startup `ScreenState` loads enabled screens into `screen_mapping`.
- The state machine will:
  - Check current page via `navigator.where_am_i()`.
  - If on a page and the target requires a different navigation mode, call `navigator.go_home()` or `navigator.manage_menu_tab(True/False)` as required.
  - Call `navigator.go_to_page(location=menu_location, in_menu_tab=uses_menu_tab)`.
  - Verify `navigator.where_am_i()` equals the expected screen name; if so, call the associated processor:
    - `Currencies` → `get_currencies()`
    - `Equipment` / `Items` → `startMatching(..., grid_type=...)`
    - `Students` → navigates to `first_student` then processes `Student` screen
    - `Student` → `get_student_info()`
- `ScreenState` tracks `visited` and `unvisited` sets and will iterate until all enabled screens are processed.

## Special cases

- Student flow:
  - `Students` is a list screen (menu_location may point to `first_student` when pressing the first entry).
  - If the `Student` entry is present and enabled, `Students` processing will trigger a subsequent navigation to `Student`.
- `ignore_page_check`:
  - Screens with `uses_menu_tab=true` may bypass the "at-page" verification since in-menu navigation is deterministic. Menu-free screens often require an explicit home check.

## Timing & tuning

- The navigator uses `Config.WAIT_TIME_MULTIPLIER` and `Config.CAPTURE_INTERVAL` to control delays.
- Recommended: use a small global action delay (for example `WAIT_BASE = 0.1`) and a larger multiplier for screen transitions (for example `SCREEN_NAV_MULTIPLIER = 3.0`). This yields faster actions with a larger margin for screen loads.
- If navigation is flaky, increase the multiplier or the capture interval.

## Troubleshooting

- If a screen never reports as reached:
  - Verify `menu_location` matches an implemented selector in `ScreenNavigator`.
  - Confirm `uses_menu_tab` is correct (wrong value will attempt the wrong navigation path).
  - Enable verbose logs and inspect `navigator.where_am_i()` output.
- If screenshots fail on Linux with AMD GPU: ensure adb `exec-out` uses stderr redirection (`screencap -p 2>/dev/null`) - this prevents stray stderr text corrupting PNG bytes.

## Adding a new screen

1. Add a new entry under `screens` with `menu_location`, `grid_type`, `uses_menu_tab`, and `enabled`.
2. Ensure `ScreenNavigator` knows how to convert `menu_location` into ADB taps/actions.
3. Add processing logic (if needed) in `screen_state.process_screen` or call existing processors that accept `grid_type`.

## Notes

- Keep `menu_location` semantic and stable; if you rename keys, update `ScreenNavigator` and tests accordingly.
- The scanner expects local data files for processors. Data sync updates local assets but does not replace config paths with URLs.

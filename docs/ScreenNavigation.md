# Screen navigation - Quick start for users

Short, practical guide so you can edit `config/screen_config.json` and understand how the scanner visits pages.

## What This File Does

`config/screen_config.json` defines which in-game screens the scanner visits, how to reach them, and whether to run extraction routines. The `launch.py` wizard manages the `enabled` flags automatically, but you can edit other fields manually if needed.

## Minimal Example

```json
{
  "Currencies": {
    "menu_location": "currencies",
    "grid_type": "currencies",
    "uses_menu_tab": false,
    "enabled": true
  }
}
```

## Key Fields

- `menu_location`: which UI control to tap (must match a selector in `ScreenNavigator.determine_button()`).
- `grid_type`: logical type passed to processors (`Equipment`, `Items`, `Students`, `Student`, `currencies`).
- `uses_menu_tab`: `true` if reached via the in-game menu tab; `false` if reached from Home.
- `enabled`: set to `false` to skip the screen during scans.

## How It Works

1. On startup, `ScreenState` loads enabled screens.
2. Ensures UI state (Home or Menu Tab).
3. Taps `menu_location`.
4. Verifies arrival, then runs the processor:
   - `Currencies` -> reads AP/Credits/Pyroxene
   - `Equipment` / `Items` -> grid scanning (`startMatching`)
   - `Students` -> taps first student -> chains to `Student` detail scanning

## Tuning Timing & Reliability

Adjust delays in `config/settings.json` (or via `launch.py -e`):

- `wait_multiplier`: Short action sleeps
- `wait_screen_nav_multiplier`: Page load & transition sleeps

**Tip**: If navigation misses screens, increase `wait_screen_nav_multiplier` first. If captures lag, increase `capture_interval`.

## Troubleshooting

- **Never reaches a screen**: Verify `menu_location` exists in `ScreenNavigator.determine_button()`. Check logs for OCR title mismatches.
- **False positives on screen detection**: Increase `wait_screen_nav_multiplier` to allow full UI renders before OCR runs.

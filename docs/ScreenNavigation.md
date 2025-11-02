# Screen navigation - Quick start for users

Short, practical guide so you can edit `config/screen_config.json` and understand how the scanner visits pages.

What this file does

`config/screen_config.json` lists the in-game pages the scanner should visit. The scanner uses that list to:
- navigate to each page
- run the appropriate data extraction or matching routine

Location

`config/screen_config.json`

Minimal example

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

Fields you care about

- `menu_location` - which UI control to tap (must match a selector in `ScreenNavigator`).
- `grid_type` - logical type passed to processors (`Equipment`, `Items`, `Students`, `Student`, `currencies`).
- `uses_menu_tab` - `true` if this screen is reached through the in-game menu tab; `false` if reached from Home.
- `enabled` - set to `false` to skip a screen temporarily.

How the scanner uses it (short)

- On startup the scanner loads enabled screens.
- For each screen it:
  1. Ensures the UI is in the right mode (Home or Menu Tab).
  2. Taps the control identified by `menu_location`.
  3. Verifies it reached the expected page, then runs the processor:
     - `Currencies` → reads currencies
     - `Equipment` / `Items` → runs matching (`startMatching`)
     - `Students` → presses `first_student` then the `Student` screen

Adding or editing screens (step-by-step)

1. Add an entry to `config/screen_config.json` with the fields above.
2. Confirm `menu_location` exists in `ScreenNavigator.determine_button()`.
   - If it doesn't exist, add the mapping (coordinate values) there.
3. If this is a new `grid_type`, update `screen_state.process_screen()` to call the correct processor.

Timing & reliability tips

- Tuning knobs are in `config.py`:
  - `WAIT_TIME_MULTIPLIER` - affects short action sleeps
  - `SCREEN_NAV_MULTIPLIER` - multiplies navigation sleeps (default: 3.0)
  - `CAPTURE_INTERVAL` - how often the screen capture thread takes images
- Quick recommended starting values:

```python
WAIT_TIME_MULTIPLIER = 0.1
SCREEN_NAV_MULTIPLIER = 3.0
CAPTURE_INTERVAL = 0.1
```

- If navigation fails often, increase `SCREEN_NAV_MULTIPLIER` first, then `CAPTURE_INTERVAL`.

Troubleshooting

- If the scanner never arrives at a screen:
  - Ensure `menu_location` is correct and present in `ScreenNavigator.determine_button()`.
  - Try increasing `SCREEN_NAV_MULTIPLIER`.
  - Check logs and `navigator.where_am_i()` output to see what the OCR detects.
- If screenshots fail to decode on Linux (AMD GPU): ensure `screencap -p` is run with stderr redirected to `/dev/null` (see `utils/device/adb_controller.py`).

That's it - edit `config/screen_config.json`, tune the timing in `config.py`, and restart the app if you change data files while the capture thread is running.

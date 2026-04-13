# Data Sync & Configuration

This project handles game data safely via local JSON files and an optional online sync mechanism. All runtime settings are managed through the `launch.py` wizard and saved to `config/settings.json`.

## Configuration Files

- `config/settings.json` -> Stores ADB host/port, wait multipliers, sync toggle, and target platform. **Managed automatically by `launch.py`.**
- `config/screen_config.json` -> Lists enabled screens, grid coordinates, and menu navigation rules.

> ⚠️ **Do not edit `config.py` directly.** It acts as a loader/model validator for `settings.json`. Manual edits will be overwritten on next launch.

## What Data Files Matter?

The processors read these local files:

- `assets/data/equipment_processed.json` - equipment definitions used for matching
- `assets/data/items_processed.json` - item definitions
- `assets/data/students_processed.json` - student metadata

If a file is missing, the app falls back to defaults. Always back up before manually replacing them.

## Data Sync

By default, the app uses local data. To enable online updates:

1. Run `python launch.py` and answer **Yes** to `Enable online data sync?`.
2. On startup, the scanner will attempt to download updated JSONs from the configured GitHub repo.
3. Files are compared via SHA256 and written atomically (`*.tmp` -> rename). If the network fails, your local files remain untouched.

### Manual Sync

- [`tools/sync_data.py`](../tools/sync_data.py) - small CLI that runs the `DataSyncManager` standalone. Use this when you want to run sync manually without starting the main app:

```bash
python -m tools.sync_data
```

## Performance Tuning (Wait Multipliers)

If your device is slow or navigation fails, adjust these in `config/settings.json` or via `launch.py -e`:

- `wait_multiplier` (default `1.0`): Scales short action delays (taps, waits between captures).
- `wait_screen_nav_multiplier` (default `2.0`): Scales navigation delays (screen loads, menu transitions).

**Recommended for laggy devices**: `wait_multiplier: 1.2`, `wait_screen_nav_multiplier: 3.0`

## Troubleshooting

- **"Sync failed"**: Check internet connection. The manager retries 3 times with backoff. Use `python -m tools.sync_data` to debug.
- **"Screens not detected"**: Increase `wait_screen_nav_multiplier`. Ensure `screen_config.json` has correct `enabled: true` flags.
- **Linux/AMD GPU screenshot corruption**: ADB's `exec-out` may leak stderr into PNG bytes. The code already handles this, but if it fails, ensure your ADB version is up to date.

## Advanced notes (if you care)

- Files are written atomically (tmp file then rename) to avoid partial writes.
- The adb screenshot bug on some Linux setups (AMD GPU) can corrupt PNG bytes. If screenshots fail to load, ensure `exec-out` uses stderr redirection:

```bash
adb -s <serial> exec-out 'screencap -p 2>/dev/null'
```

or update your local `utils/device/adb_controller.py` capture command the same way.

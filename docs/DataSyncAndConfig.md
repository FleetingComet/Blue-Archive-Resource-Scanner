# Data sync & configuration - Quick start for users

This page explains the simple, safe way this project handles its local data files and how you can configure automatic updates from remote sources.

the scanner reads local JSON files in `assets/data/`. If you run data sync, the app will try to download updated copies from a configured URL and replace the local files - it will never try to open a web URL directly.

## What files matter

- `assets/data/equipment_processed.json` - equipment definitions used for matching
- `assets/data/items_processed.json` - item definitions
- `assets/data/students_processed.json` - student metadata

Processors always read these local files. If a file is missing the app still typically falls back to bundled defaults - make a backup before forcing replacements.

## Quick user settings (what to change)

Open `config.py` and edit:

- `WAIT_TIME_MULTIPLIER` - general delay multiplier. Lower = faster, higher = more stable on slow devices. Try `0.1` for fast devices.
- `SCREEN_NAV_MULTIPLIER` - multiplies delays used for screen transitions. Default is `3.0`. If navigation is flaky, raise this value.

Example safe starting values you can paste into `config.py`:

```python
WAIT_TIME_MULTIPLIER = 0.1
SCREEN_NAV_MULTIPLIER = 3.0
CAPTURE_INTERVAL = 0.1
```

These give a good balance for many setups: short individual actions, longer delays during page loads.

## Data sync

This repository ships with local data. If you want the app to try updating that data from an online repo, do the following (recommended):


1. Configure sync sources (optional)

The `DataSyncManager` ships with reasonable built-in default URLs. You don't need to change `config.py` to use sync.

If you want to override the default remote sources or tune retries, you can set attributes on the manager directly before calling `update_from_online()`:

```python
from utils.sync.data_sync_manager import DataSyncManager

mgr = DataSyncManager()
# Replace the default list of remote files (mapping: key -> url)
mgr.remote_sources = {
  'equipment': '{your url}/equipment.json',
}
# Tune retries/backoff
mgr.retries = 3
mgr.retry_backoff = 1.0
mgr.update_from_online()
```

2. Run the data sync tool [`tools/sync_data.py`](../tools/sync_data.py) or call the `DataSyncManager` in `utils/sync/` - it will:
   - Try to download each configured URL (short timeout + retries).
   - Compare the downloaded file with the local one (SHA256). If different, it writes the new file atomically into `assets/data/`.
   - If download fails, it leaves your local files untouched.

Important: Sync never replaces config entries with URLs. The code keeps `Config.PROCESSED_DATA` as local paths so the rest of the app can open files normally.

### Utilities

- [`tools/sync_data.py`](../tools/sync_data.py) - small CLI that runs the `DataSyncManager` standalone. Use this when you want to run sync manually without starting the main app:

```bash
python -m tools.sync_data
```

- `--offline` CLI flag for `app.py` - if you run `python app.py --offline` the app will skip any network sync at startup.

## Troubleshooting

- "I changed the URL and the app still uses old data": the app only writes a new file if the content changes. Check `assets/data/` timestamps and logs.
- "Sync failed" / network errors: there is a timeout and a retry policy. If your connection is flaky, try again or increase the timeout in the sync code or manually replace them.
- "Screens aren't detected after updates": if you replace data files while a screen capture thread is running, restart the app. Also ensure `SCREEN_NAV_MULTIPLIER` is high enough for your device.

## Advanced notes (if you care)

- Files are written atomically (tmp file then rename) to avoid partial writes.
- The adb screenshot bug on some Linux setups (AMD GPU) can corrupt PNG bytes. If screenshots fail to load, ensure `exec-out` uses stderr redirection:

```bash
adb -s <serial> exec-out 'screencap -p 2>/dev/null'
```

or update your local `utils/device/adb_controller.py` capture command the same way.
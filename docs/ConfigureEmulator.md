# Configure Emulator

This short guide shows the minimal emulator settings needed to run the Blue Archive Resources Scanner.

Prerequisite: install an Android emulator and Blue Archive inside it. The scanner supports 1280x720 resolution.

1. Set emulator resolution and mode

   - Open your emulator settings.
   - Select `Tablet Mode` and set the resolution to `1280x720`.

   ![Resolution Settings](<images/Resolution Settings.png>)

2. Enable ADB on the emulator

   - If you're using BlueStacks or LDPlayer, enable the emulator's ADB setting so the host can connect.

3. MuMu Player-specific: disable Keep alive in background

   - If you're using MuMu Player 12 (or V5.8.4 as time of writing), open the instance manager and turn off `Keep alive in background` for the Blue Archive instance.

   ![Disable Keep Alive](<images/Disable Keep Alive.png>)

4. Find the emulator serial

   - The ADB serial is usually shown in the instance manager (upper-right corner) or in the emulator's multiplayer/instance list. Use that serial when you specify `ADB_HOST` / `ADB_PORT` in `config.py`.

   ![Instance Serial](images/Mumu-Serial.png)

Notes

- The scanner assumes the game is in the 1280x720 layout with no extra UI overlays or DPI scaling.
- If your emulator offers multiple DPI/scale/graphics profiles, prefer the one that matches 1280x720 and preserves UI layout.

# Credits:
[AzurLaneAutoScript Wiki](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki):
    - [Configure Emulator](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en#configure-emulator)
    - [Configure Alas](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en#configure-alas) (to get the serial values for ADB_HOST and ADB_PORT)
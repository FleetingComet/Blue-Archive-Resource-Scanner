# Blue Archive Resources Scanner

<h1 align="center">⚠️Attention: Look at dev branch if you want latest code.

</h1>

![Logo](assets/images/BA-Scanner-banner-light.png)

A Python-based tool to scan and count owned resources in **Blue Archive**.

**Resolution**: Only supports 1280x720 resolution.

> **TL;DR:** The scanner automates navigation through the game's menus to collect information that is already visible on screen. It uses screenshots and OCR to read that information and does not modify the game, memory, files, or network traffic, nor does it automate gameplay.

## Disclaimer & Scope

**Blue Archive Resource Scanner is an unofficial community-made project and is not affiliated with, endorsed by, or sponsored by Nexon or Blue Archive.**

The scanner automates navigation through relevant Blue Archive menus, captures screenshots of the information displayed by the game, and uses OCR to recognize the values shown on screen.

The resulting information is processed locally and converted into structured data for resource and inventory tracking.

### What It Does

* Automatically navigates relevant in-game menus.
* Captures screenshots of information displayed by the game.
* Uses OCR to recognize visible values (it can be inaccurate).
* Collects resource and inventory information.
* Processes the collected information locally.
* Produces structured data for resource tracking and planning.

### What It Does Not Do

* Does **not** modify the game client.
* Does **not** modify game files.
* Does **not** read or modify process memory.
* Does **not** inject code into the game.
* Does **not** intercept, inspect, or modify network traffic.
* Does **not** communicate with undocumented game APIs.
* Does **not** automate combat.
* Does **not** automate farming or stage completion.
* Does **not** automatically perform gacha or purchases.
* Does **not** automatically claim rewards.
* Does **not** attempt to bypass security or anti-cheat mechanisms.

The purpose of the automation is **information collection**, rather than playing the game on the user's behalf.

### Terms of Service

This project does not claim to be authorized, endorsed, or approved by Nexon.

Users are responsible for complying with the applicable Blue Archive/Nexon Terms of Service and other applicable policies. If you are uncertain whether using this software is permitted, please review the current official terms before using it.

### Third-Party Data

The scanner uses a separate community-maintained data repository:

* [BA-Scanner-Data](https://github.com/FleetingComet/BA-Scanner-Data)

The data in that repository includes **processed information based on Schale DB**, an unofficial database for Blue Archive maintained independently of this project.

Schale DB is an unofficial database for **Blue Archive**, developed and maintained independently of this project.

The scanner does **not** directly download game assets, game files, or proprietary data from Nexon's servers as part of this data synchronization process.

The `BA-Scanner-Data` repository is maintained separately from the scanner itself so that data updates can be distributed without requiring a new version of the scanner.

Please refer to the respective repositories and websites for their own licensing, attribution, and terms of use.

## Features

- **Scan Equipment and Item Page**: Scan and count resources in the equipment and item page.
- **Scan Student Page**: Extract levels, skill tiers, gear, UE stars, and bond levels.
- **Scan Currencies**: Scan AP, Credits, and Pyroxene.

---

## Requirements

To use the Blue Archive Resources Scanner, ensure you have the following installed:

- **Python** (I use v3.13, but version 3.8 or higher should work fine)
- **Virtual Environment** (highly recommended)

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/FleetingComet/BA-Scanner.git
   cd BA-Scanner
   ```

   (You can skip this if you want)

   1b. Create & activate a virtual environment:

   ```bash
   uv venv --python 3.13.0
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

2. Install the required Python packages (please use venv or something similar):
   ```bash
   pip install -r requirements.txt
   ```

---

## Documentation

See the docs/website index for quick links to user and developer guides:
- [https://fleetingcomet.github.io/BA-Resource-Scanner-Docs/](https://fleetingcomet.github.io/BA-Resource-Scanner-Docs/)

## Usage

### Running the Scripts

#### First Run & Configuration

The scanner now uses an interactive setup wizard. Run:

```bash
python launch.py
```

The wizard will guide you through:

1. **Platform Selection**: Emulator (MuMu, LDPlayer, etc.), Desktop Client, or Real Device.
2. **ADB Connection**: Lets you enter a custom IP/port. (Auto-fill ports coming soon)
3. **Scan Targets**: Choose which inventories to scan (`Equipment`, `Items`, `Students`, `Currencies`).
4. **Performance Tuning**: Adjust wait-time multipliers for slower devices or emulators.
5. **Data Sync**: Enable/disable automatic downloads of the latest community-maintained scanner data.

Your choices are saved to `config/settings.json` and `config/screen_config.json`. You won't need to run the wizard again unless you want to change settings.

#### Running the Scanner

- **Standard Run** (uses saved settings):
  ```bash
  python launch.py
  ```
- **Edit Configuration** (re-run wizard with current values as defaults):
  ```bash
  python launch.py -e   # or --edit
  ```
- **Force Offline Mode** (skips network sync, runs directly):
  ```bash
  python main.py --offline
  ```

Once started, the scanner automatically navigates the game, captures screenshots, extracts data using the selected OCR engine, and saves the results to the `output/` directory.

#### Output Files

After a successful scan, check the `output/` folder:

- `owned/scanned_counts.json` -> Raw item & equipment counts.
- `owned/scanned_students.json` -> Raw student stats
- `owned/scanned_currencies.json` -> AP, Credits, Pyroxene
- `equipment_final_values.json`, `items_final_values.json`, `students_final_values.json` -> Processed & mapped data ready for planning

### Exporters

### Justin163 Planner

Use the Justin163 Planner exporter to convert your scanned data and generate a file compatible with the planner:

```bash
python -m tools.justin_planner
```

The script will generate:

* **`output/justin_data_final.json`**: The converted and/or merged data compatible with Justin Planner.

#### Using an Existing Justin Planner Export

If you already have a Justin163 Planner export and want to merge it with the converted data:

1. Save your existing Justin Planner export as `justin_data.json`.
2. Place it in:
   **`input/justin_data.json`**
3. Run the exporter:

   ```bash
   python -m tools.justin_planner
   ```

The exporter will automatically use `input/justin_data.json` when available.

Alternatively, you can specify a different Justin Planner export using the `--file` option:

```bash
python -m tools.justin_planner --file path/to/justin_data.json
```

#### Optional Arguments

The exporter supports the following options:

| Option                | Description                                                                                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `-m`, `--max-target`  | Set target stats to **MAX** for newly added characters.                                                               |
| `-f`, `--file <path>` | Path to an existing Justin Planner export to merge with. Uses the default `input/justin_data.json` path when omitted. |
| `-o`, `--online`      | Download the latest community-maintained data before processing.                                                      |

For example:

```bash
python -m tools.justin_planner -m -o
```

After processing, import the generated file **`output/justin_data_final.json`** into Justin163 Planner.

---

### Midokuni Roster URL Format

Use the Midokuni exporter to convert your scanned data into a roster URL compatible with Midokuni:

```bash
python -m tools.midokuni
```

The exporter will generate the Midokuni roster URL after processing your scanned data.

#### Optional Arguments

The exporter supports the following options:

| Option                        | Description                                                      |
| ----------------------------- | ---------------------------------------------------------------- |
| `-s`, `--state <blue\|black>` | Set all characters to the specified state.                       |
| `-o`, `--online`              | Download the latest community-maintained data before processing. |

For example:

```bash
python -m tools.midokuni -s blue -o
```

---

### Schale DB Import Format

Use the Schale DB exporter to convert your scanned data into a format compatible with Schale DB:

```bash
python -m tools.schaledb
```

The exporter will generate the Schale DB import data after processing your scanned data.

#### Optional Arguments

The exporter supports the following options:

| Option           | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| `-l`, `--lock`   | Set the `lock` field to **true** for all characters.             |
| `-o`, `--online` | Download the latest community-maintained data before processing. |

For example, to mark all characters as locked:

```bash
python -m tools.schaledb --lock
```

You can also combine both options:

```bash
python -m tools.schaledb -l -o
```


---

## Roadmap

### Current Checklist:

- Read more resources (some of them needs modification, their [Search Region](/locations/search.py) are already defined)
  - [x] Credits
  - [x] Pyroxene
  - [x] Items Page, Equipment Page
  - [x] Student stats
    - [x] Skill levels (eg.: M/M/7/8)
    - [x] Unique Equipment level (is UE60?, is Level 60?)
    - [ ] the new constelation stuffs
- [ ] Different Resolution
- [x] Make screen capturing faster
- [x] More accurate and faster data reading

<!-- - [ ] Comet Haley -->
<!-- - [x] Earth (Orbit/Moon) -->

### Future Plans:

- Expand support for different resolutions (with bars and notch).
- Support other platforms (Linux) (someone tested it using waydroid)
  - Develop an Android app for convenient usage (using Kotlin, pls help I have skill issue).

---

## Credits

This project was inspired by and credits:

- [Fate/Grand Automata (FGA)](https://github.com/Fate-Grand-Automata/FGA)
- [AzurLaneAutoScript (ALAS)](https://github.com/LmeSzinc/AzurLaneAutoScript)
- [Schale DB](https://github.com/SchaleDB/SchaleDB)
- [Justin163 Planner](https://justin163.com/planner/)
- [Hina Loves Midokuni](https://hina.loves.midokuni.com/)

---

## Contributing

I welcome contributions to enhance the Blue Archive Resources Scanner. Please open an issue or submit a pull request if you'd like to help. Be sure to read the [Contribution Guide](CONTRIBUTING.md) for more information.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

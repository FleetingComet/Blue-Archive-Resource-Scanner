# Blue Archive Resources Scanner
![Logo](<assets/images/BA-Scanner_symbolon.png>)

A Python-based tool to scan and count owned resources in **Blue Archive**.

**Resolution**: Only supports 1280x720 resolution.

## Features

- **Scan Equipment Page**: Automatically scan and count resources in the equipment page.

---

## Requirements

To use the Blue Archive Resources Scanner, ensure you have the following installed:

- **Python** (I use v3.13, but version 3.8 or higher should work fine)
- **Tesseract OCR** ([Download Tesseract OCR here](https://github.com/tesseract-ocr/tesseract))

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/FleetingComet/BA-Scanner.git
   cd blue-archive-scanner
   ```
2. Install the required Python packages (please use venv or something similar):
   ```bash
   pip install -r requirements.txt
   ```
3. Install and configure **Tesseract OCR**:
   - Download and install from [Tesseract OCR GitHub page](https://github.com/tesseract-ocr/tesseract).
   - Ensure the Tesseract executable is added to your system's PATH.
   - Verify installation:
     ```bash
     tesseract --version
     ```

---

## Usage

### Configuration
Before running the scripts, ensure the configuration settings in the [`config.py`](config.py) are appropriate for your setup.  
The default settings are:
```python
ADB_HOST = "127.0.0.1" or "localhost"
ADB_PORT = 16384  # Default Mumu port
# Increase this if your device is laggy (e.g., 1.1, 1.8, or 2)
WAIT_TIME_MULTIPLIER: float = 1.0
```

Also, follow these sections from the [AzurLaneAutoScript Wiki](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki) for further configuration:
- [Configure Emulator](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en#configure-emulator)
- [Configure Alas](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en#configure-alas) (to get the serial values for ADB_HOST and ADB_PORT)

Modify the values in the [`config.py`](config.py) as needed, then proceed with the steps below.

### Running the Scripts

#### 1. Launch the Scanner Script  
Run the scanner script to generate resource files:  
```bash
python app.py
```
After running, this will generate two files:  
- **`output/owned/scanned_counts.json`**: Contains the counts of owned resources.
- **`output/owned/scanned_students.json`**: Contains your all scanned student information.
- **`output/owned/scanned_currencies.json`**: Contains the counts of your currencies (Pyrox, etc...).

- **`output/equipment_final_values.json`**: Contains the processed equipment resource values.
- **`output/items_final_values.json`**: Contains the processed items resource values.
- **`output/students_final_values.json`**: Contains the processed student values.

#### Optional
##### 1. Convert to Justin Planner Format
Use the Justin Planner converter script to prepare your data:
   ```bash
   python convert_justin_planner.py
   ```
   This script will generate:  
   - **`output/converted_to_justin_planner.json`**: A file compatible with the Justin Planner tool.
   
##### 2. Merge into Your Own Data
To merge the converted data into your existing Justin Planner export:
   1. Save your Justin Planner export as `justin_data.json`.  
   2. Place the file in the following directory:  
      **`input/justin_data.json`**  
   3. Run the merger script:  
      ```bash
      python merger_justin_planner.py
      ```  
      This script will generate:  
         - **`output/justin_data_final.json`**: The merged file containing the final combined data.  
   4. Import the generated json to Justin Planner

---

## Roadmap

### Current Checklist:

- Read more resources (some of them needs modification, their [Search Region](src/locations/search.py) are already defined)
  - [x] Credits
  - [x] Pyroxene
  - [x] Items Page
  - [x] Student stats
      - [x] Skill levels (eg.: M/M/7/8)
      - [x] Unique Equipment level (is UE50? or something)
- [ ] Different Resolution (also remove bars)
- [ ] Make screen capturing faster
- [y] More accurate and faster data reading

Note: "y" for half completed
<!-- - [ ] Comet Haley -->
<!-- - [x] Earth (Orbit/Moon) -->

### Future Plans:
  - Expand support for different resolutions (with bars and notch).
  - Make the tool more efficient and user-friendly.
  - Support other platforms (Linux and such)
    - Develop an Android app for convenient usage (using Kotlin, pls help I have skill issue).

---

## Credits

This project was inspired by and credits:

- [Fate/Grand Automata (FGA)](https://github.com/Fate-Grand-Automata/FGA)
- [AzurLaneAutoScript (ALAS)](https://github.com/LmeSzinc/AzurLaneAutoScript)
- [SchaleDB](https://github.com/SchaleDB/SchaleDB)

---

## Contributing

I welcome contributions to enhance the Blue Archive Resources Scanner. Please open an issue or submit a pull request if you'd like to help. Be sure to read the [Contribution Guide](CONTRIBUTING.md) for more information.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


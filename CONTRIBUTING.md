## Contributing  

Interested in contributing to the project? Check out the [open issues](https://github.com/FleetingComet/BA-Scanner/issues) to see where you can help.  

### Getting Started  

A basic understanding of Python is recommended. To get started with development, you'll need the following:  

- **Development Tools**: [VSCode](https://code.visualstudio.com/) or another code editor of your choice.  
- **Testing Setup**: A working emulator or Android device to test your changes.  

If you’re new to Python, you can explore the following resource:  
- [Python Beginner’s Guide](https://wiki.python.org/moin/BeginnersGuide)  

#### Steps to Contribute  

1. **Fork and Clone**: Fork the repository and clone it to your local machine.  
2. **Open the Project**: Load the project in VSCode or your preferred editor.  
3. **Create a Branch**: If working on a specific issue, create a new branch for your changes. Use the issue name for better organization:  
   ```bash
   git checkout -b issue-name
   ```  

---

## Project Structure  

- **`./src/`**: Core methods required to execute the scripts.  
- **`./assets/`**: Contains supplementary data, including the logo and other resources.  
- **`./input/ and ./output/`**:
   - `./input/`: Stores input data files required for processing.
   - `./output/`: Stores generated output files, such as processed results and converted data.
- **`./screenshots/`**: Stores screenshots, including `latest_screenshot.png`, generated using [`adb.capture_screenshot`](src/utils/adb_controller.py).
- **`.pyproject.toml and uv.lock`**: I use [UV](https://github.com/astral-sh/uv) for streamlined management of Python packages and dependencies. This tool helps automate tasks such as setting up virtual environments and installing packages.
  - **Using UV**:
    -  Create and set up a virtual environment with Python 3.13.0
            ```bash
            uv venv --python 3.13.0
            ```
    - Activate the virtual environment
            ```bash
            .\.venv\Scripts\activate
            ```
    - Install dependencies listed in the requirements.txt file
            ```bash
            uv pip install -r requirements.txt
            ```

---

## How the Scanner Works  

### Searching for Images  

When the app capture a screenshot, the following steps occur:  
1. The device takes a screenshot in its original resolution (1280x720p).  
2. The screenshot is converted to grayscale for processing.  
3. The image is cropped to focus on the relevant search region.  <!-- 4. If the reference image is in color, it’s also converted to grayscale. (This was part of the image pattern matching feature I coded in the first week of December 2024, but I decided to ditch it.) -->
4. The image is pre-processed using [preprocessor](src/utils/preprocessor.py) for OCR
5. OCR is performed on the processed image using Tesseract to extract text.  

### Handling Locations and Regions  

For more details on managing location and region coordinates, refer to this guide:  
[Contributing to FGA](https://github.com/Fate-Grand-Automata/FGA/blob/master/CONTRIBUTING.md).  

**Note**: 1440p or any other resolution is not supported yet, so the step doubling the values is unnecessary for now.  

---
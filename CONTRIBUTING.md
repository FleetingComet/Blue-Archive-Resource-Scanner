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
4. **Make Your Changes**: Implement your fixes or features.
5. **Commit and Push**: Commit your changes with a descriptive message, then push your branch to your fork.
6. **Create a Pull Request**: Open a pull request against the main repository and describe your changes.

---

## Project Structure  

- **`./utils/`**: Core methods required to execute the scripts.  
- **`./assets/`**: Contains supplementary data, including the logo and other resources.  
- **`./input/`**: Stores input data files required for processing.
- **`./output/`**: Stores generated output files, such as processed results and converted data.
<!-- - **`./screenshots/`**: Stores screenshots, including `latest_screenshot.png`, generated using [`adb.capture_screenshot`](/utils/adb_controller.py). -->
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
3. The image is cropped to focus on the relevant search region ([extract.py](utils/ocr/extract.py)).
4. The cropped image is processed differently depending on the type of element being detected:
    - **gear**: The cropped image is converted to grayscale and matched against known gear tier image patterns.
    - **star**: The cropped image is analyzed to detect star shapes, which may indicate rarity or rating.
    - **ue_star**: Specific background colors are removed from the cropped image to isolate blue stars, then the image is matched using a blue star detection algorithm.
    - **ue_level**: Non-white colors are removed from the cropped image to isolate level numbers for easier OCR.
    - **number_in_circle**: Only a specific color (hex `3c4e66`) is retained to help extract numbers displayed inside colored circles.
    - **Other types**: The image may be pre-processed in other ways depending on the context.
5. The processed image is further pre-processed using [preprocessor.py](utils/ocr/preprocessor.py) to optimize it for OCR.
5. OCR is performed on the processed image using Tesseract to extract text.  

### Handling Locations and Regions  

For more details on managing location and region coordinates, refer to this guide:  
[Contributing to FGA](https://github.com/Fate-Grand-Automata/FGA/blob/master/CONTRIBUTING.md).  

**Note**: 1440p or any other resolution is not supported yet, so the step doubling the values is unnecessary for now.  

---

# Handling Screen Navigation
Developer-specific screen navigation details are available at [`docs/dev/ScreenNavigationReference.md`](docs/dev/ScreenNavigationReference.md) in this repository.
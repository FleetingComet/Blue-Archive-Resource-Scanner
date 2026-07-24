# Changelog


All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-07-24

### Bug Fixes

- **Fix window region detection and screenshot cropping** ([`ba5b1d7`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ba5b1d7e8bd39f149531983b45169daac8e52068) - 2026-07-14)
  - Improve client region calculation by using GetClientRect and ClientToScreen instead of manual border offset calculations.
  - Add support for minimized windows and fix image cropping logic.
  - The previous implementation had incorrect array indexing and didn't properly account for window borders

- **Fix imports and refactor main processing flow** ([`1d5b2c7`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1d5b2c7c901d611fc37d60f10845c7b1b5c558f4) - 2026-07-14)
  - Fixed absolute imports across modules (workers, extract) for consistency
  - Improved project root path detection in Config to dynamically locate main.py
  - Added conditional post-processing that only runs processors on successfully visited screens

- **Fix import paths and remove unused imports** ([`27b3ec0`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/27b3ec09b00349d30068c316a4d0a91bead24612) - 2026-07-13)
  - Fix scanner import in state.py to use proper module path (src.services.scanner instead of direct scanner import).
  - Remove unused Dict import from typing in data_sync_manager.py

- **Fix FloatPrompt parameter and refactor settings loading** ([`face2e0`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/face2e0a9e8899f8f5048d5ed2e3b1275042fb32) - 2026-07-13)
  - Add explicit `default=` parameter to FloatPrompt.ask() call
  - Rename `previous` to `previous_settings` for clarity
  - Move `load_screens_from_config()` logic earlier to apply consistently across all code paths (first launch, edit mode, and regular startup)



### Documentation

- **Refactor constants, add debug mode, switch to rapidocr** ([`cfabb6b`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/cfabb6be1c32fb1a2c4bbe4892d31c198229f5b1) - 2026-07-20)
  - Move screen configuration to dedicated constant module for better organization.
  - Refactor CLI argument parsing to use argparse and add --debug flag support. Increase navigation wait times for more reliable screen transitions. Fix file link format in scanner output and remove unused OCR import

- **Update README.md** ([`9fb6026`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/9fb60263123eb47afb8215a1fd313898e5e02145) - 2026-07-16)



### Features

- **Add DPI awareness and fix window offsets** ([`4787813`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/47878134e2b5368d498c080a706a24ff77a6afce) - 2026-07-20)
  - Enable DPI awareness to handle high-DPI displays correctly with fallback support.
  - Disable cursor capture in WindowsCapture to avoid cursor artifacts.
  - Fix window cropping offset calculation to use client coordinates directly instead of derived calculations, improving accuracy

- **Add gear tier text extraction support** ([`4eff6c1`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/4eff6c1c247fabb6b2d2d383f9e96d40b988ab9f) - 2026-07-20)
  - Implements gear tier level extraction for OCR processing.
  - Adds `get_tier_level()` function to parse tier formats (e.g., 'T9', 'T7'), handling in `ExtractionMode.GEAR` with specialized preprocessing (upscaling and color filtering for tier indicators).
  - Also renames `get_lv()` to `get_talent_level()` for clarity and fixes docstring typo

- **Add new extraction modes and add debug config** ([`96022e3`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/96022e3150beab23874cf5a00e3588c6ed734276) - 2026-07-19)
  - Replace string-based image_type parameter with enum-based ExtractionMode for type safety and consistency.
  - Add DEBUG flag to Config temporarily for conditional debug behavior.
  - Enhance logging with rich markup formatting for better terminal output.
  - Create enums package __init__.py file and update docstrings to reflect the new enum-based API

- **Add retry logic and refactor state machine** ([`e76b112`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e76b112c9a3fd6dc92470a02e7a39d2a1379456b) - 2026-07-16)
  - Implement tenacity-based retry mechanism for navigation resilience.
  - Replace print statements with structured logging using Rich.
  - Simplify FSM by consolidating states and removing redundant verification steps.
  - Add Progress bar for better UX feedback
  - Improve OCR text matching for menu tab detection with case-insensitivity and partial matching



### Maintenance

- **Cleanup search.py, make Gear into Enum** ([`e338485`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e338485479ae90013639913a649e14868c919731) - 2026-07-20)
  - Remove unnecessary comments.
  - Update the workers.py's student worker to follow Gear Enum updates

- **Move things to src folder** ([`3d7ad13`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/3d7ad13a8d07f49d81a4a7e8816c7bd39fa47a33) - 2026-07-13)



### Refactoring & Improvements

- **Refactor OCR extraction flow and move text utilities** ([`093a6c0`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/093a6c0c25e7fb2ee6b7ad5bdef8a6bf801cd9c8) - 2026-07-20)
  - Reorganize the OCR extraction flow by moving `get_tier_level()` from engine.py to text_util.py where it belongs.
  - Restructure extract.py to defer gear tier extraction until after text processing.
  - Improve preprocessor.py by consolidating mode-specific preprocessing before general conversion, making the logic clearer and easier to maintain.
  - Remove unused imports and simplify conditional logic

- **Refactor Config to ConfigManager with direct attribute access** ([`ea989cc`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ea989ccff3401a62e7cff438e01bc702084b1142) - 2026-07-19)
  - Convert Config from static class with dictionary-based path access to ConfigManager instance with direct attributes. Changes include:
  - Refactored Config class to ConfigManager with instance initialization
  - Replaced nested dictionaries (OWNED, PROCESSED_DATA, OUTPUT_FILES) with direct instance attributes (scanned_counts, equipment_processed, final_items, etc.)
  - Extracted path resolution logic into _locate_root() and directory creation into _ensure_directories() methods
  - Updated all modules (scanner, processors) to use new attribute-based access
  - Fixed enum property access by removing unnecessary .value suffixes
  - Added debug_mode setting and utility function imports for JSON handling

- **Waits, buttons** ([`5c753f5`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/5c753f575b321aa404e4e158ab7f6fc8dbf4a257) - 2026-07-19)
  - Refactor ScreenNavigator to centralize navigation logic and clean up template/OCR helpers.
  - Added BUTTON_MAP and KNOWN_SCREENS constants, a _wait helper to standardize sleep multipliers, and _check_asset_in_region for image-template checks. identify_screen, ensure_at_home, ensure_menu_state, at_home, at_page and determine_button were simplified and loops were made more robust

- **Improve menu/page detection and template matching** ([`cfea8c8`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/cfea8c8752ac52e55baffafdb911429b992529ea) - 2026-07-19)
  - Add backups of replaced menu/home assets and switch to region class MENU_REGION in screens.
  - Refactor navigator to retry taps when navigating home, and add retries to ensure_menu_state (now accepts max_attempts).
  - Increase detection thresholds and show debug crops when enabled.
  - Replace match_image_using_file with find_template_location which returns a Region on success (or None) and add logging.
  - Minor cleanup in match_image_using_directory logging

- **Refactor OCR to use ExtractionMode enum, Fix Rarity Detection (Yellow Star)** ([`cf0d704`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/cf0d704089182ab81dc58e756c41c9a88ce2a493) - 2026-07-19)
  - Introduce ExtractionMode enum.
  - Update extract_from_region and preprocess_image_for_ocr to accept modes; convert callers across services/workers/scanner.
  - Improve image matching: make matchers use Path, handle template resizing, grayscale checks and error cases.
  - Add robust star counting (count_stars) and adjust star utilities/debug output paths.
  - Misc: navigator asset paths and fuzzy title matching, add logging in main and device factory, small scanner logic fix, and update .gitignore entries

- **Make menu detection case-insensitive** ([`920de36`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/920de36fe46c423520daae3449dfda86c421230c) - 2026-07-18)
  - Fix is_menu to check for 'menu' in the already-lowercased text instead of 'Menu'.
  - The previous case-sensitive check could miss matches after normalization; this change makes menu detection consistent and prevents false negatives

- **Refactor logging with custom formatters and error handling** ([`657faa9`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/657faa94afb81b5525417eff2520b1217a7bd67a) - 2026-07-18)
  - Implement a dual-handler logging system with a custom PlainTextFormatter that strips Rich markup for file logs while keeping Rich formatting for console output.
  - Replace print statements with proper logging throughout swipe utilities.
  - Improve error messages with exception details and ensure navigation recovery after errors.
  - Reorganize utility modules into proper package structure

- **Unify device abstraction layer** ([`3a53e8c`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/3a53e8c3be4ac9da700b9ad418fa969af8a6e6bd) - 2026-07-14)
  - Consolidate separate InputController and ScreenshotProvider abstractions into a single DeviceController interface. This simplifies the device interaction layer by combining screenshot capture and input operations.
  - Changes:
  - Replace InputController with unified DeviceController interface
  - Add ADBDevice and DesktopDevice implementations
  - Add WindowManager for desktop window coordinate handling
  - Update navigator, state, and scanner to use new interface
  - Remove legacy abstraction files (ADBScreenCapture, DesktopScreenCapture, WindowCapture variants)
  - Add factory pattern for device creation
  - Update type hints throughout

- **Refactor settings and add device factory** ([`1bb4662`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1bb4662c3a0df4ecd4df2abc1e8b85fe94180bda) - 2026-07-14)
  - Rename UserSettings to AppSettings for clarity and add TargetPlatform enum to replace string-based platform selection.
  - Introduce a device factory function to handle creation of appropriate device controllers (Desktop, ADB) based on the target platform setting. Update launch wizard to use enum values for consistency

- **Extract OCR workers to separate module** ([`340129d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/340129dfc50c46a6e48c8bb3b7571c7fa9020c52) - 2026-07-14)
  - Refactor OCR worker functions out of scanner.py into a new workers.py module for better code organization and maintainability.
  - Add TypedDict for ItemResult to improve type safety

- **Use Rich's IntPrompt and FloatPrompt** ([`4cd3d1e`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/4cd3d1ea09205e1b1266090db9184c1b90482eb5) - 2026-07-13)
  - Replace custom ask_int() and ask_float() functions with Rich library's built-in IntPrompt and FloatPrompt classes.
  - Also updates the UserSettings import path to src.core.config

<!-- generated by git-cliff -->
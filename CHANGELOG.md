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

- **Image resizing logic in OCR matcher** ([`cdc4a6f`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/cdc4a6fc667ee0c01bd1564a9d8664e0046ca7a2) - 2026-06-27)
  - Move image resizing logic outside the grayscale condition block.
  - The resizing of small images should apply regardless of whether grayscale conversion is enabled, not just when grayscale is True.
  - This fixes a logic error where small non-grayscale images would not be properly upscaled

- **Sync condition check** ([`70136ce`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/70136ce0709307ea534c8895023fdc445667307d) - 2026-06-27)
  - Corrected the configuration setting checked when determining whether to sync data.
  - The code was checking `offline_mode` instead of `enable_sync`, which would have prevented syncing from working as intended

- **Fix path handling and improve screencap reliability** ([`be8ea02`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/be8ea0272568c1395f442e1bb9a7c1ea5e299ee1) - 2025-11-02)
  - Corrected path concatenation in config.py and data_sync_manager.py to use Path objects consistently, preventing potential path errors. Updated ADBController to handle screencap command differently on Unix-like systems, redirecting stderr to avoid malformed PNGs due to known issues

- **Fix default file init and improve value parsing** ([`ae9fd01`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ae9fd013b7f5310b1658e56dae600500bc27c0fa) - 2026-04-13)
  - Change _ensure_file default from a list to a dict to match expected file initialization.
  - Improve OCR value parsing: normalize_skill_value now delegates to normalize_value so strings like "MAX" and formats like "Lv.7" are handled consistently.
  - normalize_value now handles None, strips input, removes non-digit characters (e.g. "Lv.7", "T9", "81"), returns a configurable default when parsing fails, and catches specific exceptions for safer behavior

- **Fix data not merging** ([`a53594a`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/a53594acf9096d0ee5fc9c289dea7a454ecc8970) - 2025-05-23)

- **Fix errors** ([`32c973d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/32c973d9dff7703480e8e465cda0adc2ba8ceb92) - 2025-03-17)



### Documentation

- **Refactor constants, add debug mode, switch to rapidocr** ([`cfabb6b`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/cfabb6be1c32fb1a2c4bbe4892d31c198229f5b1) - 2026-07-20)
  - Move screen configuration to dedicated constant module for better organization.
  - Refactor CLI argument parsing to use argparse and add --debug flag support. Increase navigation wait times for more reliable screen transitions. Fix file link format in scanner output and remove unused OCR import

- **Update README.md** ([`9fb6026`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/9fb60263123eb47afb8215a1fd313898e5e02145) - 2026-07-16)

- **Update README.md** ([`c4ff6f0`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/c4ff6f077f8899eeb89ea71fdae1f4f7f27de346) - 2026-06-27)

- **Add user and developer documentation for emulator, data sync, and navigation** ([`a9851ff`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/a9851ff32d256359a95fb954041552960bc3b8a3) - 2025-11-02)
  - Added new documentation files covering emulator configuration, data sync, and screen navigation for both users and developers. Updated README with documentation links and improved setup instructions. CONTRIBUTING.md now references the developer navigation guide. These changes provide clearer guidance for configuring, running, and extending the scanner

- **Docs revamp, RapidOCR integration, requirements.txt update** ([`b7cc3b2`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/b7cc3b2123ea26fba4c731d335fe0c144aa41be1) - 2026-04-13)
  - Revise documentation and onboarding (CONTRIBUTING, README, docs/*) to clarify setup, interactive launcher usage, config files, screen navigation, and data sync.
  - Replace external Tesseract dependency with RapidOCR (update in launch.py) and refresh requirements.txt to add rapidocr, onnxruntime and other supporting packages while removing pytesseract.
  - Also cleaned up examples, formatting, and added guidance for performance tuning and emulator/config workflows

- **Integrate RapidOCR engine and replace Tesseract** ([`def5dd3`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/def5dd3cef16adaf9309072212cfa4f4f0bd1f80) - 2026-04-10)
  - Add RapidOCR models and config, plus a thin engine wrapper to lazily initialize RapidOCR and extract text with error handling (utils/ocr/engine.py).
  - Replace direct pytesseract/cv2 usage in utils/ocr/extract.py to call the new extract_text, and simplify preprocessing/branching logic.
  - Update screen_navigator imports/usages to use the new engine.
  - Comment out a broken matching call for Equipment/Items in screen_state.
  - Also add THIRD_PARTY_LICENSES.md referencing RapidOCR license

- **Update documentation** ([`4041116`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/40411161e73a4ce2584b08994112e19e7ada84b5) - 2025-06-01)

- **Update docs** ([`65d9af8`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/65d9af8c82db2adf1502bb6d35864a6339bd9988) - 2025-03-16)

- **Update Docs** ([`ba0cf8a`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ba0cf8a25a72621ec7fa713c60090d6d3e1fb62e) - 2025-03-09)
  - and convert wip

- **Update README.md** ([`f7f22af`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/f7f22af934ee6a81390920977c3f989cbea29d49) - 2025-01-31)

- **Adjust some code and add documentation** ([`c5811e2`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/c5811e2aac15c31eb13607e1b0adab684b67bee4) - 2025-01-30)

- **Update Docs** ([`180fc36`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/180fc36ea2a9ba771b4546b704a8f206f10104bb) - 2024-12-17)

- **Update Docs** ([`f8e2213`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/f8e221373df7271818f7ca8a4949a3febc92559d) - 2024-12-17)

- **Update README.md** ([`ff81c46`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ff81c46838d54c390d159ee0dc31675b3f111411) - 2024-12-15)
  - oops I forgot to add SchaleDB I'm sorry (μ_μ)

- **Update README.md** ([`f2e73cb`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/f2e73cbe746ed2a9934a83cd709dd72d962c02bf) - 2024-12-15)
  - Add Contribution guide link



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

- **Add adaptive blue star counter and tweak OCR/regions** ([`cf066cd`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/cf066cd9d05223547d06bde397a49dd717159ae2) - 2026-06-07)
  - Introduce a new adaptive star-counting utility and hook it into OCR extraction.
  - Added utils/ocr/star_util.py implementing count_blue_stars_adaptive to robustly detect blue stars (works for tiny crops and larger images).
  - Updated utils/ocr/extract.py to import and use the new function for "ue_star" cases, removed some unused imports and older color-removal code, and simplified preprocessing paths.
  - Adjusted STAR_QUANTITY region in locations/search.py to better match UI coordinates.
  - Also updated .gitignore to ignore test.png and test.py

- **Add new Entry point for Non Techy users** ([`d4bf0fc`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/d4bf0fcf85c0c80c7dbe7f4877167c32880ad5bd) - 2026-03-27)

- **Add offline mode and improve data sync handling** ([`b1c3b75`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/b1c3b75d7189bce74fa8f28e928236e8a0a8e2f7) - 2025-11-02)
  - Introduces an --offline flag to skip data sync and network calls in app.py, and refactors path_init to support this. Adds a CLI tool (tools/sync_data.py) for running DataSyncManager independently. Enhances DataSyncManager with retry logic, atomic file updates, and improved error handling. Adds SCREEN_NAV_MULTIPLIER to Config and applies it to screen navigation delays for better control on slower devices

- **Add text matcher and IO utilities; replace Levenshtein** ([`9467875`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/94678751992f75c5ffcdcf3d1058131944e9b9ba) - 2026-04-09)
  - Introduce a rapidfuzz-based text matcher and simple JSON IO helpers, and update processors to use them.
  - Add utils/data/text_matcher.py implementing find_closest using rapidfuzz.process.extractOne.
  - Add utils/data/io.py with read_json, write_json, update_count, and update_student helpers and tests (tests/test_io.py).
  - Replace direct Levenshtein usage in utils/data/item.py, equipment.py, and student.py with find_closest; simplify fuzzy matching logic.
  - Add tests for fuzzy matching (tests/test_text_matcher.py).
  - Remove utils/data/__init__.py (deleted empty module).
  - These changes remove the direct Levenshtein dependency in favor of rapidfuzz and add small utilities and tests to improve reliability and maintainability

- **Add ordering & random helpers to Location/Region** ([`b87c508`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/b87c508b8bcd3e65b02753a4361d5c1040e49bcb) - 2026-04-02)
  - Introduce ordering and utility methods for Location and Region: add total_ordering for Location with __lt__ and __eq__, add center/right/bottom properties that return the point itself, and a random_point method that returns a jittered Location. Import random and total_ordering. For Region, add __gt__, contains_point, and random_point_in_region which returns the region center plus a random offset. These helpers simplify comparisons and provide convenient randomized point selection

- **Add base-res scaling & adjust desktop input/swipe** ([`7bd102a`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/7bd102a5313040ce659a2d7f96a2e83bfb64dee1) - 2026-03-29)
  - Introduce coordinate scaling from a base resolution (Size 1280x720) to the current window capture: import Size, add _scale_from_base and test_translate_from_base_resolution helpers, and update tap_xy to scale coordinates before clicking. Add debug prints in tap_test. Update DesktopInputController to call controls.tap_xy with game coords and use controls.swipe for swipes. Also increase swipe_utils sample_height from 100 to 630 to sample a larger area when comparing frames. These changes make input clicks/swipes resolution-aware and improve swipe difference sampling

- **Add grid_config, load screens & refactor capture** ([`48ce04c`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/48ce04c7eb8c6472c673d741c26dc5bc9af3785f) - 2026-03-29)
  - Add per-screen grid_config (or explicit None) for several screens in launch.py and introduce load_screens_from_config to restore enabled screens from screen_config.json when reusing saved settings. Refactor main.py to unify capture/input backends: import get_adb_components/get_desktop_components, create platform-specific screencap and input_controller, start the screencap (sc) and pass input_controller to ScreenNavigator. Remove the old desktop helper and reorganize ADB connection/start logic to support emulator/device/desktop targets

- **Add input controllers and unify capture backend** ([`b9b582f`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/b9b582fb7efd5be3ca4caa62703a11374d61526d) - 2026-03-29)
  - Introduce a unified input abstraction and refactor desktop screenshot handling.
  - Add InputController (abstract) and concrete implementations: ADBInputController and DesktopInputController.
  - Add DesktopControls helper (pyautogui) for window-aware input on desktop.
  - Extend swipe utilities: import InputController, add swipe_with_verification and helper _screens_are_different to retry swipes using screenshots.
  - Refactor capture_backend to return platform-specific ScreenshotProvider and InputController, plus helper factories get_desktop_components/get_adb_components and _get_window_capture_backend to share WindowCapture instances.
  - Update DesktopScreenCapture to accept an injected window_capture_backend (allow sharing) and small API/formatting fixes.
  - These changes unify input handling across Android (ADB) and desktop, enable reuse of window capture backends to avoid duplication, and add robust swipe verification to improve reliability

- **Add retrying on ADB Connect** ([`c4fedf5`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/c4fedf51db0a1c8e4adf8a3090e5915e1236be1e) - 2025-06-01)

- **Add auto updater for processed data** ([`c75bd89`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/c75bd8908a1ae1e35bb89eb56524a6dee30cd18c) - 2025-05-12)
  - from https://github.com/FleetingComet/BA-Scanner-Data

- **Add Currencies to scanner** ([`0f501fd`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/0f501fd267e359b7c39d00411386ad92e1a9027d) - 2025-03-09)

- **Add trained data** ([`175d3cf`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/175d3cf5d2d2d71558a137d2fdd5e6e7b4faf732) - 2025-02-15)

- **Add item data from SchaleDB** ([`5d4df38`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/5d4df38f109046a92a8a2a7559eb943c52c37dd1) - 2025-02-15)

- **Add location switching (wip)** ([`be1c5b6`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/be1c5b6714bd765b80a12d02b43146334d0c1719) - 2025-01-23)
  - will optimize when it's working now
  - items scanning soon™

- **Add more locations and regions** ([`ca879c6`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ca879c6ca799f33f409b939d0382f21920fd3eec) - 2025-01-23)

- **Add merge to your own Justin planner data** ([`8d74353`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/8d7435310059d48832e61aa99b74a17e13948904) - 2024-12-17)



### Maintenance

- **Cleanup search.py, make Gear into Enum** ([`e338485`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e338485479ae90013639913a649e14868c919731) - 2026-07-20)
  - Remove unnecessary comments.
  - Update the workers.py's student worker to follow Gear Enum updates

- **Move things to src folder** ([`3d7ad13`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/3d7ad13a8d07f49d81a4a7e8816c7bd39fa47a33) - 2026-07-13)

- **Update requirements.txt** ([`aa29e52`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/aa29e52113d9c8ec61ca27064b89c96c222f28ba) - 2026-07-13)

- **Clean-up** ([`f2dc3dd`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/f2dc3dd8b3bc6050f8681782e1df778bf5158368) - 2026-06-06)

- **Clean up and reorganize imports** ([`7568a30`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/7568a30509f9424ca86ca91c31f3e8026484699d) - 2026-04-13)

- **Move things part 2** ([`b7dfd43`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/b7dfd438a0448a91f45c4274b20efac4ad471954) - 2025-04-01)

- **Move things** ([`00c9ae7`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/00c9ae79f9d05f2ee9acc6bee770f95db02ce67e) - 2025-04-01)

- **Moved to own repo** ([`ac8cb34`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ac8cb34fef12842ddb51d44b0f268224a41cb376) - 2025-03-27)
  - https://github.com/FleetingComet/BA-Scanner-Data

- **Move dev tools to own repo or something** ([`206ff2c`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/206ff2ccc25559f93541f6956cd6e373fd63d2c7) - 2025-03-27)



### Other Changes

- **Add changelog and update deps** ([`a0a8b60`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/a0a8b60a1608fbbaf948f97464f92f6c8806386e) - 2026-07-24)
  - Add CHANGELOG.md documenting project history and cliff.toml configuration for automated changelog generation, update package name to use hyphens for consistency, and update/add dependencies including rapidocr, tenacity, rich, and other modernized packages

- **Update merger_justin_planner.py** ([`7e4d1ed`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/7e4d1edb46acf22867ccc12e2294b1a10dc97122) - 2026-07-07)

- **Image resizing logic in OCR matcher"** ([`1880682`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1880682074fe0c9a283df8d261857814970ba236) - 2026-06-27)
  - This reverts commit cdc4a6fc667ee0c01bd1564a9d8664e0046ca7a2

- **Data update** ([`2cadfcd`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/2cadfcdaf51a97a748e77a5e48a3342a3e3c47b3) - 2026-06-27)

- **UE 60** ([`39bd393`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/39bd393ebb3581ff130f65bb18e749e57249a373) - 2026-06-07)

- **Update Data** ([`795e4e9`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/795e4e99eaab0dfcfdb992ebc2b8ce521871bcff) - 2026-03-27)

- **Rename app.py to main.py** ([`27a531b`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/27a531b52a1f78af0f1d1e570a1397c6dded53e1) - 2026-03-27)
  - also add temporary function to test things

- **Renge Name fix** ([`6f93d53`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/6f93d534695c19b0ce491c89a588920501e4bf14) - 2025-08-03)
  - fixes https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/issues/7

- **Update app.py** ([`fc2c3ef`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/fc2c3efa7c48ad533c7dd01eb9871d9fc4054ec8) - 2025-07-19)
  - Revise logic, not tested

- **Update screen_state.py** ([`478efa8`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/478efa84ff145c5f50d1dd254ca91e5e6c684832) - 2026-04-13)
  - Uncomment it so we can use it

- **THIRD_PARTY_LICENSES** ([`f318893`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/f318893b6158e6834ba6423fdcc2409cd29248c1) - 2026-04-10)

- **Parallelize OCR and refactor scanner I/O** ([`c15282d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/c15282d797f8cff56f68de7b754f252aeba20784) - 2026-04-10)
  - Introduce threaded OCR workers and refactor scanner flow to capture screenshots first and process them later.
  - Added _ocr_image_worker and _ocr_student_worker, use tempfile dirs to store captured detail/student screenshots, and process them with concurrent.futures to improve OCR throughput.
  - Reworked startMatching and get_student_info to save detail images during navigation (reduced wait times, more robust capture/exit checks) and then aggregate OCR results, deduplicate student records, and persist using utils.data.io (read_json/write_json/update_count).
  - Also replaced several direct updates (update_name_owned_counts/update_character_data) with batched writes and improved error handling for capture/OCR failures

- **Logging, menu, matching** ([`e4936b9`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e4936b9fb5d753ac58a6fd12c26662e9126df316) - 2026-04-10)
  - Rename the file log from fsm_navigation.log to scanner_state.log for clearer naming. Simplify menu handling by passing cfg["uses_menu_tab"] directly to ensure_menu_state instead of branching; keep ensure_at_home when the config is false. Re-enable startMatching for Equipment/Items (remove debug print and restore matching call with grid_type and grid_config). These changes clean up debug output and restore intended matching behavior

- **Some fixes** ([`118370c`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/118370c9a80f16b559ca906b7f3dd8991272312f) - 2026-04-10)

- **Update jsonHelper.py** ([`9ac1942`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/9ac194216ec82182ab1eff3c8184d3ecf794389d) - 2026-04-09)
  - well to fix my stupidity lol

- **Update screen_state.py** ([`59f5382`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/59f5382419c380c894fa7c486fb8b4f168d22402) - 2026-04-09)
  - add skip navigation when we are already on certain page

- **Reorganize imports** ([`7573c5d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/7573c5da33cae054a85451c83e2cb17bbe07c6d3) - 2026-04-08)

- **Detect empty slots via color match** ([`1cc417e`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1cc417ea8d0d4ed6021284afbd73bab4f6610ca4) - 2026-04-08)
  - Replace previous stddev-based empty-region check with a color-matching approach. Renames is_item_empty to is_empty_slot and adds parameters for empty_slot_hex (default "c4cfd4"), per-channel tolerance, and coverage_threshold (fraction of pixels that must match). Imports hex_to_bgr, handles ROIs with alpha channel, builds an inRange mask around the target BGR color, and returns true when matching_ratio >= coverage_threshold

- **Added more questions** ([`a727e1d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/a727e1d43868bcdf922b77eb4c0a465f9401d6cb) - 2026-04-08)

- **Update base.py** ([`48caac1`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/48caac13a796416a98e5a6c1c27d0688e4fa6d3d) - 2026-04-02)
  - aaaa

- **Update item_util.py** ([`750193a`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/750193a8026d7a1c212d9602f271f6ebe982400c) - 2026-04-02)
  - TODO

- **Adjust search region coords and handle Currencies** ([`b2ae2e0`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/b2ae2e0b7ed06d5218a81b6fa61b668ce7a0bf61) - 2026-04-02)
  - Tweaks search Region coordinates for AP, CREDIT, and PYROXENE to better match the UI offsets (updated AP, CREDIT, PYROXENE values and left original values commented). Adds a special-case in ScreenState.process_screen for the "Currencies" screen: the Currencies coordinates is on the Home page, ensure we're at Home, process the screen immediately, update visited/unvisited sets, and avoid the usual menu navigation. Includes a short delay and

- **Tap random Region points; update determine_button** ([`7c65baf`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/7c65baf0706d462bed66d5faa1f041e8a7ae85a8) - 2026-04-02)
  - Rename determine_button parameter from `location` to `region` and change its return type from Optional[Location] to Optional[Region]. Update docstring and lookup to use the new `region` key. Callers (go_home and manage_menu_tab) now obtain a random point via `random_point_in_region()` and tap using `point.x/point.y` instead of the region's fixed x/y; add a type annotation for `button` in manage_menu_tab and adjust debug prints accordingly

- **Replace ADBController with InputController** ([`9e9aa92`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/9e9aa92db86d88dc3af5b4fe78f6306bac44c55f) - 2026-03-29)
  - Refactor scanner.py to use a platform-agnostic InputController instead of ADBController. Updated imports and replaced capture_screenshot and tap/execute_command calls with input_controller methods. startMatching signature now accepts input_controller and optional grid_config (with sensible defaults), uses a config dict for grid parameters, and uses swipe_with_verification for scrolling. get_student_info and get_currencies were updated to accept input_controller

- **Uncomment functions oopsie teehee~** ([`36cf520`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/36cf5203d4c59e4e11bbcaa025e5c203d7e5929d) - 2025-06-01)

- **Update from schale db** ([`fee948d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/fee948d36fa2f1bec34ada691a6ebd8cc1e3fe9d) - 2025-06-01)

- **Merge pull request #5 from FleetingComet/dev** ([`6459fae`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/6459faed90502a612766b3db402d5fa696b1f37c) - 2025-05-12)
  - Dev

- **Merge branch 'main' into dev** ([`d6bbd46`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/d6bbd46b2b23eefb791645f49313a2e266ee1e01) - 2025-05-12)

- **Update data** ([`296ac21`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/296ac21ff5e8680f6daf81d63577fd451bc2121a) - 2025-05-12)

- **Update screencapture** ([`74e635e`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/74e635ec1cb5ba521203a3df035358d8fbb58ce1) - 2025-05-12)

- **Create adbscreencapture.py** ([`d1368d6`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/d1368d6c6ee1885a521dfc4538b05f5e406ce981) - 2025-05-12)

- **Update goToLocation -> Screen Navigator** ([`f0eea4a`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/f0eea4ab47f2819dbdf1cf3d56dc99a282a82e0f) - 2025-05-12)
  - also migrated to OOP

- **Update convert_justin_planner.py** ([`9817c9c`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/9817c9c26beb7ab8d4e1cb216621e1edb425de49) - 2025-05-12)
  - Updated to use OOP

- **Aaa** ([`d67a528`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/d67a528b8931628a5e04878ea6f0f35f5504ddc8) - 2025-04-01)

- **Update app.py** ([`db55281`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/db552819c6b0069fa5377b12e351b39a5f3587b9) - 2025-03-23)
  - Temporary fix

- **Update Assets from SchaleDB** ([`59d356d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/59d356d43cc760d9a80eae414dcbc1d76b8c4748) - 2025-03-23)

- **Merge branch 'main' into dev** ([`aee7785`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/aee7785b3b3ddb6bd2d6f94f518fd10a34c8adb6) - 2025-03-17)

- **Merge branch 'main' into dev** ([`72a80fc`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/72a80fca4fff3dbbda6e957c5eee92d275350cca) - 2025-03-16)

- **Update convert_justin_planner.py** ([`bc73265`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/bc732658c7e1c1e4b5016894a281b8f4c8c05114) - 2025-03-16)

- **Align Item test result** ([`2dffe24`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/2dffe24d1c19d44719806091fa65c591c3235914) - 2025-03-16)

- **Use Pathlib for paths** ([`d5df5e2`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/d5df5e2c93e37c3f8ed457b233f91801194e146a) - 2025-03-16)

- **Enum fix** ([`30e8eec`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/30e8eec0994d66b17e73e63d35d3955de4151511) - 2025-03-07)

- **Code clean up part 2** ([`4042fd2`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/4042fd297dcfdb8c31cc54b0059d0404f90e9a81) - 2025-03-07)

- **Code cleanup** ([`8c239c3`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/8c239c3e9f35a87634e98fff881e98f358fbf7ec) - 2025-03-07)

- **Update Skill regions** ([`ace97b8`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ace97b8196d9282984d79146a79d890fe93c0d76) - 2025-03-07)

- **Create item_util.py** ([`671a389`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/671a389c22453f9541cb00871269d3d238c5cfc2) - 2025-02-28)
  - for future

- **Dev (#2)** ([`ef92957`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ef9295738e23f67455db6b2d1ce7068aa54a3be1) - 2025-02-15)
  - add location switching (wip)
  - will optimize when it's working now
  - items scanning soon™
  - Code clean up on `goToLocation`
  - Use what I learned lol (the walrus operator so the python version will be 3.8 minimum)
  - also reverse if logic for cleaner code
  - Adjust some code and add documentation
  - Separation of Concerns
  - Better logic at looping items
  - Finish up location switching
  - I disabled `Items` because of name inconsistencies (I need trained data for tesseract or use other OCR idk) but it works
  - swiping is inconsistent idk why pls help
  - Update README.md
  - Update search.py
  - More Search Patterns
  - swipe_utils: Slower Swipe
  - it should be treated as drag (2000ms)
  - if it's short it's a fling (below 300ms)
  - Update scanner.py
  - adjust wait time for longer swipe
  - Update what I use
  - also allow ascii characters (JP text)
  - Add item data from SchaleDB
  - Adjust Item name search region
  - Add trained data
  - Adjust Config names
  - naming is hard
  - Enable Item Process

- **Merge branch 'main' into dev** ([`aee4fa6`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/aee4fa6b02e6487cb9c9e0f18ee0263f9b8c0487) - 2025-02-15)

- **Enable Item Process** ([`2e4f489`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/2e4f4898ef161f4f196475edf49097688917830f) - 2025-02-15)

- **Adjust Config names** ([`e126200`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e1262006320700d71571ee4f67c036e9fbbb00c0) - 2025-02-15)
  - naming is hard

- **Adjust Item name search region** ([`4ff024e`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/4ff024ed8a1918e31e4eee6b3abeaa580080b35c) - 2025-02-15)

- **Update what I use** ([`a1bdf4e`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/a1bdf4e4ef58043a21e5d5f236757a529100d636) - 2025-02-15)
  - also allow ascii characters (JP text)

- **Update scanner.py** ([`be8600d`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/be8600d9788fb84a6fa0f61bd22c0dd089fe5bd9) - 2025-02-15)
  - adjust wait time for longer swipe

- **Slower Swipe** ([`2701d54`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/2701d542b1c4e60569429ea7c71c60e46ee2ddb3) - 2025-02-15)
  - it should be treated as drag (2000ms)
  - if it's short it's a fling (below 300ms)

- **Update search.py** ([`3e58897`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/3e58897d43f2864e8b5ad4d5b1ed391d584c6387) - 2025-02-12)
  - More Search Patterns

- **Dev (#1)** ([`8888e69`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/8888e6991753bc50d6ca60de84c65d8f990036ba) - 2025-01-31)
  - add location switching (wip)
  - will optimize when it's working now
  - items scanning soon™
  - Code clean up on `goToLocation`
  - Use what I learned lol (the walrus operator so the python version will be 3.8 minimum)
  - also reverse if logic for cleaner code
  - Adjust some code and add documentation
  - Separation of Concerns
  - Better logic at looping items
  - Finish up location switching
  - I disabled `Items` because of name inconsistencies (I need trained data for tesseract or use other OCR idk) but it works
  - swiping is inconsistent idk why pls help
  - Update README.md

- **Finish up location switching** ([`fe4fd97`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/fe4fd97e4098e61841c091150c12da02bb14622e) - 2025-01-31)
  - I disabled `Items` because of name inconsistencies (I need trained data for tesseract or use other OCR idk) but it works
  - swiping is inconsistent idk why pls help

- **Better logic at looping items** ([`11660d9`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/11660d977911d9b15984a916d98eb6d44bbd9cfd) - 2025-01-31)

- **Separation of Concerns** ([`e744742`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e74474223d9156f8b6557f09615ab01821157d42) - 2025-01-31)

- **Code clean up on `goToLocation`** ([`28a3a07`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/28a3a078fc407a3842641e3409f6b8a0de35011f) - 2025-01-30)
  - Use what I learned lol (the walrus operator so the python version will be 3.8 minimum)
  - also reverse if logic for cleaner code

- **Update JSON processor** ([`0662649`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/066264925c20df55a6ceadeded68fca81e096b5b) - 2025-01-23)

- **Upload what I use** ([`5ed9bed`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/5ed9bed616c4d0569ef27bb7e24935d6e63fc12d) - 2025-01-23)

- **Upload Script** ([`03b8500`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/03b85008134eab940a83db207374e6720bcd5e04) - 2024-12-15)

- **Upload assets** ([`4122c34`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/4122c34c39f7d59cf18deca65a07064ece6ca0d8) - 2024-12-15)

- **Initial commit** ([`1067342`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1067342a4a03d53d99e2df779838163b2674e344) - 2024-12-15)



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

- **Refactor launcher wizard and screen config** ([`69868fd`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/69868fd663e7395a105e0d197ce6360d7a069b74) - 2026-03-29)
  - Rename offline_mode → enable_sync and overhaul launcher/wizard flow. Added SCREEN_DEFAULTS, USER_FACING_SCREENS and a write_screen_config() helper that three-way merges on-disk config with code defaults and the launcher-enabled choices. Reworked run_wizard() prompts and defaults ( clearer platform/device wording, wait-time guidance, default screens fallback ), and persist/apply chosen screens via write_screen_config(). Introduced _parse_args() to support --edit/-e to force reconfiguration, changed first-run vs saved-settings behavior to skip the wizard when appropriate, and adjusted launch to respect the new enable_sync flag. Minor formatting and messaging improvements. Updated main.py to use the settings sync flag when deciding whether to run DataSyncManager

- **Pydantic settings and dynamic paths** ([`2ce0785`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/2ce0785566e6a1b1fb900c43adb2451a6dde64ed) - 2026-03-27)
  - Replace the old Config class with a pydantic-based UserSettings model and a new Config instance that loads/saves settings from config/settings.json. Introduces typed settings (adb_host, adb_port, wait_multiplier, screen_nav_multiplier, capture_interval, offline_mode, target_platform). Converts many static class path constants into instance-managed directories, ensures directories are created at init, and centralizes file paths (owned, processed, output, screenshots). Also adds load_settings/save_settings helpers and creates a global Config instance

- **Refactor window capture and improve backend selection** ([`1ec1ac2`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1ec1ac26903346721cb5e378b62b244ea41cd685) - 2025-08-03)
  - New WindowsCapture backend
  - NiiightmareXD's windows-capture and moved the original implementation to window_capture_backup.py.
  - Updated DesktopScreenCapture to dynamically select the appropriate window capture backend based on the operating system and their availability.
  - Minor formatting and code cleanup blablba etc..

- **Refactor screen navigation** ([`1b17341`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/1b173417eef7e70a4edcd7e01ffebf6a2af4422b) - 2025-07-20)
  - Replaces manual screen navigation logic in app.py with a new ScreenState state machine, which loads screen configuration from config/screen_config.json and manages navigation and processing for each enabled screen. Adds screen_state.py to encapsulate navigation and processing logic

- **Refactor scanning, swipes, and screenshot handling** ([`ee9ecb8`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/ee9ecb8ac99244555ed678e1127ecf4ff975d470) - 2026-04-13)
  - Remove launcher_settings.json and refactor scanner, input capture, and swipe utilities.
  - scanner.py: add normalize_value parsing, stop scanning when an empty slot is detected, use randomized tap points, adjust swipe coordinates, reduce some waits, and improve OCR result handling before writing counts.
  - utils/device/inputs/*: return .copy() of screenshots to avoid shared-memory/mutable view issues.
  - utils/device/swipe_utils.py: remove old standalone swipe/verify helpers and update swipe_with_verification signature/logic to use explicit start/end Y coordinates, verify using the full grid region (with debug diff_ratio), and tweak swipe parameters

- **Refactor screen navigation, config, and FSM** ([`5a3e21e`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/5a3e21e69e1fed76e42f464d8b9d144ac6e6b3ed) - 2026-04-08)
  - Large refactor across navigation, config, launch, scanner and screen-state logic:
  - area.py: rename Region.random_point_in_region -> random_point for a simpler API.
  - config.py: rename screen navigation multiplier keys to wait_screen_nav_multiplier and update Config attribute names.
  - launch.py: persist/load screen config as a flat mapping (no outer "screens" key), fix JSON handling, reorder/import small CLI tweaks, and wire renamed wait_screen_nav_multiplier throughout the wizard.
  - screen_navigator.py: major refactor - add NavigationResult dataclass, rename where_am_i -> identify_screen, consolidate OCR/title extraction, introduce ensure_at_home/ensure_menu_state/navigate_to_target flows, unify timing to the renamed wait_screen_nav multiplier, use Region.random_point, simplify image-matching to operate on crops.
  - screen_state.py: introduce a NavState FSM with logging, improved config loading (auto-inject student config), retry/fallback logic, chaining Students -> Student flow, and an executor that processes screens; also made startMatching commented out for testing.
  - These changes aim to make navigation more robust and testable, centralize timing/config names, improve logging/observability, and prepare for more deterministic state handling and retries

- **Use Region for UI locations and add type hints** ([`aae0593`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/aae0593923e82e90f700b1299bfc527b23783ab1) - 2026-04-02)
  - Replace single-point Location values with Region (bounding box) definitions across entrypoint and screens modules to represent UI areas more accurately. Remove unused Location import, adjust coordinates/sizes (e.g. menu tabs, home, students, menu tab title), and add simple type annotations for attributes (StudentInfo.BUTTONS, StudentList.FIRST_STUDENT, Home.MENU_BUTTON, Page.HOME_BUTTON). Also reorganize StudentInfo BUTTONS into an inner class with annotated PREVIOUS/NEXT

- **Use InputController and ScreenshotProvider** ([`29404ed`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/29404eda612e01032fae9b27d77f1ee5002428b0) - 2026-03-29)
  - Replace direct ADB/ADBScreenCapture usage with a higher-level InputController and optional ScreenshotProvider. Add _get_screenshot helper and safer screencap start checks, switch all input taps to input_controller.tap, and use ScreenshotProvider.get_latest_screenshot when available. Clean up OCR region handling and formatting, and propagate grid_config through ScreenState: include grid_config in screen metadata, pass it into process_screen, and forward it to startMatching. Overall this decouples device I/O for easier testing and alternative capture implementations

- **Refactor some parts of the code** ([`68f38ac`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/68f38ac45e878af5114cc17f284815de81e06c10) - 2025-03-16)

- **Improve Screen Switcher and add Student List Info** ([`92671f5`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/92671f5611176fd205ab24cda32b2b0a6c1e4ffd) - 2025-03-09)



### Work in Progress

- **Add Talent Search** ([`7efb546`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/7efb546aeea328e70539f0d2e075d69c2619795e) - 2026-06-06)
  - Add support for extracting student talent levels.
  - Define TALENT regions in locations/search.py and wire talent OCR outputs into scanner._ocr_student_worker.
  - Implement a specialized OCR path in utils/ocr/engine.py (extract_text_talent + get_lv regex) and use it from utils/ocr/extract.py.
  - Map extracted talent fields into character data in utils/data/jsonHelper.py. Minor formatting/comment tweaks applied in several files

- **[WIP] Add desktop capture** ([`5437230`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/5437230511217e140e39d7c02dd0475cf9b6ec0f) - 2025-07-20)
  - Adds WindowCapture and WindowCaptureMSS for desktop window capture, DesktopScreenCapture for threaded desktop capture, and updates ADBScreenCapture to inherit from ScreenshotProvider. Includes a backend selector

- **Dev (#4)** ([`4ea7311`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/4ea731179090fd765a59dafad539665bc2bb1226) - 2025-03-17)
  - add location switching (wip)
  - will optimize when it's working now
  - items scanning soon™
  - Code clean up on `goToLocation`
  - Use what I learned lol (the walrus operator so the python version will be 3.8 minimum)
  - also reverse if logic for cleaner code
  - Adjust some code and add documentation
  - Separation of Concerns
  - Better logic at looping items
  - Finish up location switching
  - I disabled `Items` because of name inconsistencies (I need trained data for tesseract or use other OCR idk) but it works
  - swiping is inconsistent idk why pls help
  - Update README.md
  - Update search.py
  - More Search Patterns
  - swipe_utils: Slower Swipe
  - it should be treated as drag (2000ms)
  - if it's short it's a fling (below 300ms)
  - Update scanner.py
  - adjust wait time for longer swipe
  - Update what I use
  - also allow ascii characters (JP text)
  - Add item data from SchaleDB
  - Adjust Item name search region
  - Add trained data
  - Adjust Config names
  - naming is hard
  - Enable Item Process
  - Create item_util.py
  - for future
  - Student Info WIP
  - Update Skill regions
  - Student Info WIP Part 2
  - Code cleanup
  - Code clean up part 2
  - Student Info WIP Part 3
  - enum fix
  - Student Info WIP Final
  - Will fix the screen switcher later
  - Improve Screen Switcher and add Student List Info
  - Add Currencies to scanner
  - Update Docs
  - and convert wip
  - Config: use Pathlib for paths
  - Refactor some parts of the code
  - Align Item test result
  - Update convert_justin_planner.py
  - Update docs
  - Fix errors

- **Dev (#3)** ([`be717cc`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/be717cc11231a6a5586f283a3b6de2c05e6f1b57) - 2025-03-16)
  - add location switching (wip)
  - will optimize when it's working now
  - items scanning soon™
  - Code clean up on `goToLocation`
  - Use what I learned lol (the walrus operator so the python version will be 3.8 minimum)
  - also reverse if logic for cleaner code
  - Adjust some code and add documentation
  - Separation of Concerns
  - Better logic at looping items
  - Finish up location switching
  - I disabled `Items` because of name inconsistencies (I need trained data for tesseract or use other OCR idk) but it works
  - swiping is inconsistent idk why pls help
  - Update README.md
  - Update search.py
  - More Search Patterns
  - swipe_utils: Slower Swipe
  - it should be treated as drag (2000ms)
  - if it's short it's a fling (below 300ms)
  - Update scanner.py
  - adjust wait time for longer swipe
  - Update what I use
  - also allow ascii characters (JP text)
  - Add item data from SchaleDB
  - Adjust Item name search region
  - Add trained data
  - Adjust Config names
  - naming is hard
  - Enable Item Process
  - Create item_util.py
  - for future
  - Student Info WIP
  - Update Skill regions
  - Student Info WIP Part 2
  - Code cleanup
  - Code clean up part 2
  - Student Info WIP Part 3
  - enum fix
  - Student Info WIP Final
  - Will fix the screen switcher later
  - Improve Screen Switcher and add Student List Info
  - Add Currencies to scanner
  - Update Docs
  - and convert wip
  - Config: use Pathlib for paths
  - Refactor some parts of the code
  - Align Item test result
  - Update convert_justin_planner.py
  - Update docs

- **Student Info WIP Final** ([`a5e9ff0`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/a5e9ff0be67445ea6e7bed49d035f15f8607c4fc) - 2025-03-09)
  - Will fix the screen switcher later

- **Student Info WIP Part 3** ([`e35646c`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/e35646cc88e6e7996c9659ecaec638a6b60037b7) - 2025-03-07)

- **Student Info WIP Part 2** ([`3e061ff`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/3e061ff31f118865a40295259b7c8de08098fa84) - 2025-03-07)

- **Student Info WIP** ([`77c76e3`](https://github.com/FleetingComet/Blue-Archive-Resource-Scanner/commit/77c76e3c7fac867ac1525d768eca38e2147e6835) - 2025-03-04)


## v1.0.0 - 2026-07-24

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
import os
import cv2

import json
from enum import Enum

from test_matcher import match_template
from region import Region

with open(r"patterns/equipments.json", "r") as f:
    patterns_data = json.load(f)
    print(json.dumps(patterns_data, indent=4))


def create_enum(name, data):
    return Enum(name, {k.upper(): v for k, v in data.items()})


class ImagePattern(Enum):
    HAT = create_enum("Hat", patterns_data["Hat"])
    GLOVES = create_enum("Gloves", patterns_data["Gloves"])
    SHOES = create_enum("Shoes", patterns_data["Shoes"])
    BAG = create_enum("Bag", patterns_data["Bag"])
    BADGE = create_enum("Badge", patterns_data["Badge"])
    HAIRPIN = create_enum("Hairpin", patterns_data["Hairpin"])
    AMULET = create_enum("Amulet", patterns_data["Charm"])
    WRISTWATCH = create_enum("Wristwatch", patterns_data["Watch"])
    NECKLACE = create_enum("Necklace", patterns_data["Necklace"])
    EXP = create_enum("Exp", patterns_data["Exp"])


def test_patterns(patterns_dir, screenshots_dir, results_dir, threshold=0.8):
    """
    Automates testing of image patterns against screenshots.

    Args:
        patterns_dir (str): Path to the directory containing patterns.
        screenshots_dir (str): Path to the directory containing screenshots.
        results_dir (str): Directory to save test results (visualizations/logs).
        threshold (float): Confidence threshold for template matching.
    """
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)

    # Load all patterns
    for category in ImagePattern:
        category_enum = category.value
        for tier, pattern_path in category_enum.__members__.items():
            pattern_file = os.path.join(patterns_dir, pattern_path.value)
            if not os.path.exists(pattern_file):
                print(f"Pattern file missing: {pattern_file}")
                continue

            print(f"\nTesting pattern: {category.name.lower()} {tier.lower()}")

            # Load all screenshots
            for screenshot_file in os.listdir(screenshots_dir):
                screenshot_path = os.path.join(screenshots_dir, screenshot_file)

                # Match template
                region: Region = match_template(screenshot_path, pattern_file, threshold)

                # Log results
                result_log = os.path.join(results_dir, "test_results.txt")
                with open(result_log, "a") as log:
                    if region:
                        log.write(
                            f"{pattern_file} matched in {screenshot_file} at {region.center}\n"
                        )
                        print(f"Matched in {screenshot_file} at {region.center}")
                        # Save a visualization
                        visualize_match(
                            screenshot_path,
                            region,
                            results_dir,
                            pattern_file,
                            screenshot_file,
                        )
                    else:
                        log.write(f"{pattern_file} not found in {screenshot_file}\n")
                        print(f"Not matched in {screenshot_file}")


def visualize_match(image_path, region, results_dir, pattern_file, screenshot_file):
    """
    Visualizes matched region and saves the result.

    Args:
        image_path (str): Path to the main image.
        region (Region): The matched region.
        results_dir (str): Directory to save visualization.
        pattern_file (str): Name of the pattern file.
        screenshot_file (str): Name of the screenshot file.
    """
    image = cv2.imread(image_path)
    if not region:
        return

    # Draw rectangle on matched region
    cv2.rectangle(
        image, (region.x, region.y), (region.right, region.bottom), (0, 255, 0), 2
    )

    # Save visualization
    pattern_name = os.path.basename(pattern_file).split(".")[0]
    screenshot_name = os.path.basename(screenshot_file).split(".")[0]
    result_file = os.path.join(results_dir, f"{pattern_name}_in_{screenshot_name}.png")
    cv2.imwrite(result_file, image)
    print(f"Visualization saved: {result_file}")


if __name__ == "__main__":
    # Paths
    patterns_dir = r"assets/equipments"
    screenshots_dir = "screenshots"
    results_dir = "tests/test_results"

    # Run tests
    test_patterns(patterns_dir, screenshots_dir, results_dir)

import cv2
import os
import json


def select_and_save_multiple_patterns(image_path, save_dir, coordinates_file):
    """
    Allows the user to select multiple patterns (regions) from an image, save them as individual files,
    and save their coordinates to a JSON file.

    Args:
        image_path (str): Path to the input image.
        save_dir (str): Directory to save the cropped patterns.
        coordinates_file (str): Path to the JSON file for saving coordinates.
    """
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.fastNlMeansDenoising(image)

    if image is None:
        print("Error: Unable to load the image. Check the file path.")
        return

    # Create the directory to save patterns if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    # Dictionary to store coordinates with pattern filenames
    coordinates_data = {}

    pattern_count = 0  # Counter for naming saved patterns

    while True:
        # Display the image and let the user select an ROI
        print("Select a region of interest (ROI) and press ENTER or SPACE to confirm.")
        print("Press ESC to exit the selection process.")
        roi = cv2.selectROI("Select Pattern", image, showCrosshair=True)

        # Check if ESC is pressed (ROI will return all zeros)
        if roi == (0, 0, 0, 0):
            print("No region selected. Exiting.")
            break

        # Extract the selected region
        x, y, w, h = map(int, roi)
        pattern = image[y : y + h, x : x + w]

        # Save the cropped pattern with a unique filename
        pattern_filename = os.path.join(save_dir, f"pattern_{pattern_count}.png")
        cv2.imwrite(pattern_filename, pattern)
        print(f"Pattern {pattern_count} saved to: {pattern_filename}")

        # Store the coordinates along with the filename
        coordinates_data[pattern_filename] = {"x": x, "y": y, "width": w, "height": h}

        # Increment the pattern counter
        pattern_count += 1

        # Ask if the user wants to continue
        print("Continue selecting? (Close the window or press ESC to finish.)")

    # Close the ROI selection window
    cv2.destroyAllWindows()

    # Save the coordinates data to the JSON file
    with open(coordinates_file, "w") as json_file:
        json.dump(coordinates_data, json_file, indent=4)
    print(f"Coordinates saved to '{coordinates_file}'.")
    print(
        f"Selection process completed. {pattern_count} patterns saved in '{save_dir}'."
    )


if __name__ == "__main__":
    # Define the image path, output directory, and coordinates file
    # image_path = r"image\equipment.png"      # Input image
    image_path = "screenshots/latest_screenshot.png"      # Input image
    # image_path = r"image\item_technotes_yellow.png"  # Input image
    # image_path = r"assets\equipments\equipment_icon_hat_tier2_piece.webp"  # Input image
    save_dir = "image/patterns"  # Directory to save patterns
    coordinates_file = "data/coordinates.json"  # JSON file to save coordinates

    # Run the multi-pattern selection and save process
    select_and_save_multiple_patterns(image_path, save_dir, coordinates_file)

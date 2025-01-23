import cv2
import os

from locations.equipments import EquipmentPattern


def select_and_save_multiple_patterns(image_path, save_dir):
    """
    Allows the user to select multiple patterns from an image and save them based on predetermined names
    according to the JSON scheme.

    Args:
        image_path (str): Path to the input image.
        save_dir (str): Directory to save the cropped patterns.
    """
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.fastNlMeansDenoising(image)

    if image is None:
        print("Error: Unable to load the image. Check the file path.")
        return

    # Create the directory to save patterns if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    while True:
        # Prompt user to select a category and tier
        print("\nAvailable Categories:")
        for category in EquipmentPattern:
            print(f"- {category.name.lower()}")

        category_name = input("Select a category (e.g., gloves): ").upper()
        if category_name not in EquipmentPattern.__members__:
            print(f"Invalid category: {category_name}")
            continue

        # category_enum = ImagePattern[category_name].value
        # print(f"\nAvailable Tiers for {category_name}:")
        # for tier in category_enum:
        #     print(f"- {tier.name.lower()}")

        tier_name = input("Select a tier (e.g., t1): ").upper()
        # if tier_name not in category_enum.__members__:
        #     print(f"Invalid tier: {tier_name}")
        #     continue

        # Determine the filename
        filename = f"{category_name.lower()}_{tier_name.lower()}.png"
        save_path = os.path.join(save_dir, filename)

        # Display the image and let the user select an ROI
        print(
            "\nSelect a region of interest (ROI) and press ENTER or SPACE to confirm."
        )
        print("Press ESC to cancel the selection.")
        roi = cv2.selectROI("Select Pattern", image, showCrosshair=True)

        # Check if ESC is pressed (ROI will return all zeros)
        if roi == (0, 0, 0, 0):
            print("No region selected. Exiting.")
            break

        # Extract the selected region
        x, y, w, h = map(int, roi)
        pattern = image[y : y + h, x : x + w]

        # Save the cropped pattern
        cv2.imwrite(save_path, pattern)
        print(f"Pattern saved as: {filename}")

        # Ask if the user wants to continue
        print("\nContinue selecting? (Close the window or press ESC to finish.)")

    # Close the ROI selection window
    cv2.destroyAllWindows()
    print(f"Selection process completed. Patterns saved in '{save_dir}'.")


if __name__ == "__main__":
    image_path = r"image/equipment.png"  # Input image
    save_dir = r"assets/equipments"  # Directory to save patterns

    select_and_save_multiple_patterns(image_path, save_dir)

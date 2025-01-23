import cv2
import os

from utils.adb_controller import ADBController

screenshots_dir = "screenshots"
screenshot_path = os.path.join(screenshots_dir, "latest_screenshot.png")

adb_controller = ADBController()

if not adb_controller.capture_screenshot(screenshot_path):
    print("Failed to capture screenshot.")
    
# Load the image

image = cv2.imread(screenshot_path)

# Starting coordinates and dimensions
start_x, start_y = 690, 160
item_width, item_height = 110, 90 #90
cols_per_row = 5
y_padding = 11 #10

# Output directory
output_dir = "item_templates"
os.makedirs(output_dir, exist_ok=True)

# Variables for iteration
count = 0
current_y = start_y

# Process each row
while True:
    current_x = start_x
    for col in range(cols_per_row):
        # Define the cropping region
        x_start = current_x
        y_start = current_y
        x_end = x_start + item_width
        y_end = y_start + item_height

        # Ensure we don't go out of bounds
        if y_end > image.shape[0] or x_end > image.shape[1]:
            break

        # # Crop the item
        item = image[y_start:y_end, x_start:x_end]
        
        # Further crop to center region
        crop_h = round((y_start + y_end) / 2)
        crop_w = round((x_start + x_end) / 2)

        # Adjust bounds for the final crop (20x20 region around the center)
        #h 10, y 20
        final_y_start = crop_h - 20
        final_y_end = crop_h + 20
        final_x_start = crop_w - 30
        final_x_end = crop_w + 30

        # Ensure bounds stay within the image size
        final_y_start = max(0, final_y_start)
        final_y_end = min(image.shape[0], final_y_end)
        final_x_start = max(0, final_x_start)
        final_x_end = min(image.shape[1], final_x_end)

        item = image[final_y_start:final_y_end, final_x_start:final_x_end]

        # Save the cropped image
        output_path = os.path.join(output_dir, f"item_{count + 1}.png")
        cv2.imwrite(output_path, item)
        count += 1

        # Move to the next column
        current_x += item_width

    # Move to the next row
    current_y += item_height + y_padding

    # Break if we've reached the bottom of the image
    if current_y + item_height > image.shape[0]:
        break

print(f"Extracted {count} items and saved to '{output_dir}'")
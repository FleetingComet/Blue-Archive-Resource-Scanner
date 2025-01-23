import cv2
import pytesseract
from PIL import Image
import os
import json

# Load the image
image_path = "testimage\equipment.png"
image = cv2.imread(image_path)

# Grid dimensions based on visual inspection
item_width = 113
item_height = 98
columns = 5
rows = 4

# Create output directory
output_dir = "extracted_items"
os.makedirs(output_dir, exist_ok=True)


# Function to extract text using OCR
def extract_text_from_image(cropped_image):
    # Convert the cropped image to RGB (Tesseract works better with PIL images)
    pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    # Perform OCR
    text = pytesseract.image_to_string(pil_image, config="--psm 6").strip()
    return text


# Extract and label each cell
item_data = []
for row in range(rows):
    for col in range(columns):
        # Calculate the region for each cell
        x = (685 + col * item_width) - (2 * col)
        y = 158 + row * item_height
        cropped = image[y : y + item_height, x : x + item_width]

        # Extract text label using OCR
        label = extract_text_from_image(cropped)
        label = label.replace("\n", " ")  # Clean up label

        # Separate Tier label from numeric value
        tier_label = None
        numeric_value = None

        if "T" in label:
            parts = label.split()
            tier_label = parts[0]
            # numeric_value = float(parts[1])
            numeric_value = parts[1]
        else:
            # numeric_value = float(label)
            numeric_value = label

        # Save the cropped image with the expected file name
        output_filename = f"item_{row}_{col}.png"
        output_path = os.path.join(output_dir, output_filename)
        cv2.imwrite(output_path, cropped)

        # Append to item data
        item_data.append(
            {
                "row": row,
                "col": col,
                "label": label,
                "tier_label": tier_label,
                "numeric_value": numeric_value,
                "image_path": output_path,
            }
        )

        print(f"Extracted and labeled: {output_filename}")

mapping_file = os.path.join(output_dir, "item_mapping.json")
with open(mapping_file, "w") as f:
    json.dump(item_data, f, indent=4)

print(f"Extraction complete! Item data saved to {mapping_file}.")

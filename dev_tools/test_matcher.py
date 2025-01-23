import cv2

from matcher import create_region_from_match

# Paths to the image and template
# image_path = r"image\equipment.png"
image_path = "screenshots/latest_screenshot.png"
# template_path = r"image\patterns\pattern_5.png" #hat
template_path = "assets/equipments/hat_t7.png"  # orb purple
# template_path = r"image\patterns\pattern_0.png"  # hat t2 piece processed
# template_path = r"assets\equipments\equipment_icon_badge_tier1.webp"  # badge t1
# template_path = r"assets\equipments\equipment_icon_hat_tier2.webp"  # hat t2
# template_path = r"assets\equipments\equipment_icon_hat_tier2_piece.webp"  # hat t2 piece


image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
cv2.imshow("Detected Region", image)
cv2.waitKey(0)
matched_region = create_region_from_match(template_path, image, threshold=0.6)

cv2.rectangle(
    image,
    (matched_region.x, matched_region.y),
    (matched_region.right, matched_region.bottom),
    (0, 255, 0),
    2,
)

center_coordinates = (int(matched_region.center.x), int(matched_region.center.y))
print(center_coordinates)
scale_factor = 0.7  # Adjust this as needed to see the image comfortably
cv2.circle(image, center_coordinates, 10, (0, 0, 255), -2)
image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)
cv2.imshow("Detected Region", image)
cv2.waitKey(0)
cv2.destroyAllWindows()


def visualize_match(image_path, region):
    image = cv2.imread(image_path)
    cv2.rectangle(image, (region.x, region.y), (region.right, region.bottom), (0, 255, 0), 2)
    cv2.imshow("Matched Region", image)
    cv2.waitKey(0)

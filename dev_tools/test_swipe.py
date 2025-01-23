from utils.adb_controller import ADBController


adb_controller = ADBController()
start_x, start_y = 690, 160
item_width, item_height = 110, 90  # 90
cols_per_row = 5
y_padding = 11  # 10
swipe_distance = 490 + (item_height + y_padding)

adb_controller.execute_command(
    f"shell input swipe {start_x + item_width} {swipe_distance} {start_x + item_width} {start_y} 500"
)
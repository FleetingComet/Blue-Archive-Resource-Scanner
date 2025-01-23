


from utils.adb_controller import ADBController


if __name__ == "__main__":

    # adb_controller = ADBController(host="192.168.254.156", port=5037)
    adb_controller = ADBController(host="localhost", port=16384)
    if adb_controller.connect():
        print("Connected")
    else:
        print("Not Connected")
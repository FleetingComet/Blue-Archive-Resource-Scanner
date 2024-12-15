from config import Config
from equipment import process_equipment
from scanner import startMatching
from src.utils.adb_controller import ADBController

if __name__ == "__main__":
    # device connected (not emu) example:
    # adb_controller = ADBController(host="192.168.254.156", port=5037)
    # Mumu Emulator is the default
    # adb_controller = ADBController()
    isFinished = False

    adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)
    if adb_controller.connect():
        isFinished = startMatching(adb_controller)
    else:
        print("Failed to connect to ADB. Exiting.")

    if not isFinished:
        print("Matching process failed or was interrupted.")

    # Process Equipment
    process_equipment()

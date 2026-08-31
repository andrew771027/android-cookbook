import json

from android_cookbook.adb import list_devices
from android_cookbook.shell import get_current_user, get_kernel_info, get_working_directory, list_root_directory

def main() -> None:

    devices = list_devices()

    online_devices = [
        device 
        for device in devices
        if device.state == 'device'
    ]

    if not online_devices:
        raise RuntimeError("No Android device available")
    
    serial = online_devices[0].serial

    info = {
        "serial": serial,
        "user": get_current_user(serial),
        "cwd": get_kernel_info(serial),
        "kernel": get_kernel_info(serial),
        "root_directories": list_root_directory(serial),
    }

    print(
        json.dumps(
            info,
            indent=2
        )
    )

if __name__ == "__main__":
    main()
import json
from dataclasses import asdict
from typing import List

from android_cookbook.adb import AdbDevice, get_property, list_devices
from android_cookbook.properties import collect_device_properties


def collect_device_info(serial: str) -> dict[str, str]:
    return {
        "serial": serial,
        "model": get_property(serial, "ro.product.model"),
        "android_version": get_property(serial, "ro.build.version.release"),
        "sdk": get_property(serial, "ro.build.version.sdk"),
        "build": get_property(serial, "ro.build.id"),
    }


def main() -> None:
    devices: List[AdbDevice] = list_devices()

    online_devices = [device for device in devices if device.state == "device"]

    if not online_devices:
        raise RuntimeError("No Android device available")

    target_device: AdbDevice = online_devices[0]
    target_serial = target_device.serial

    target_properties = collect_device_properties(target_serial)

    result = {"serial": target_serial, **asdict(target_properties)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

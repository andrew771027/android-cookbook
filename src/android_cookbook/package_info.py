import argparse
import json

from android_cookbook.adb import list_devices
from android_cookbook.package_manager import (
    get_package_path,
    package_exists,
)


def get_online_serial() -> str:

    devices = [device for device in list_devices() if device.state == "device"]

    if not devices:
        raise RuntimeError("No Android device available")

    return devices[0].serial


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package",
        required=True,
        help="pacjage name is required.",
        default="com.android.settings",
    )

    args = parser.parse_args()

    package_name = args.package

    serial = get_online_serial()

    exists = package_exists(
        serial,
        package_name,
    )

    result = {
        "serial": serial,
        "package": package_name,
        "installed": exists,
        "apk_paths": [],
    }

    if exists:

        path = get_package_path(
            serial,
            package_name,
        )

        result["apk_paths"] = path.paths

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

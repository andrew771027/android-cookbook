import subprocess
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str


def run_adb(*args: str) -> str:
    command = ["adb", *args]

    result = subprocess.run(command, capture_output=True, text=True, check=True)

    return result.stdout.strip()


def list_devices() -> List[AdbDevice]:
    output = run_adb("devices")

    devices: List[AdbDevice] = []

    for line in output.splitlines()[1:]:
        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) < 2:
            continue

        serial = parts[0]
        state = parts[1]

        devices.append(AdbDevice(serial=serial, state=state))

    return devices


def get_property(serial: str, property_name: str) -> str:
    return run_adb("-s", serial, "shell", "getprop", property_name)

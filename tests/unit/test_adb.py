import subprocess

from android_cookbook.adb import AdbDevice, get_property, list_devices


def test_list_devices(monkeypatch):
    adb_output = """List of devices attached
emulator-5554	device
ABC123	device
"""

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=adb_output, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    actual = list_devices()

    expected = [
        AdbDevice(serial="emulator-5554", state="device"),
        AdbDevice(serial="ABC123", state="device"),
    ]

    assert actual == expected


def test_list_devices_with_offline_devices(monkeypatch):
    adb_output = """List of devices attached
emulator-5554	device
ABC123	offline
"""

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=adb_output, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    actual = list_devices()

    expected = [
        AdbDevice(serial="emulator-5554", state="device"),
        AdbDevice(serial="ABC123", state="offline"),
    ]

    assert actual == expected


def test_get_property(monkeypatch):

    captured_command = None

    def fake_run(command, **kwargs):

        nonlocal captured_command

        captured_command = command

        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout="Pixel 10\n", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    actual = get_property(serial="ABC123", property_name="ro.product.model")

    assert actual == "Pixel 10"

    assert captured_command == [
        "adb",
        "-s",
        "ABC123",
        "shell",
        "getprop",
        "ro.product.model",
    ]

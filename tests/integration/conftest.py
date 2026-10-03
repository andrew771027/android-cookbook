from pathlib import Path

import pytest

from android_cookbook.adb import list_devices
from android_cookbook.package_manager import package_exists, uninstall_package

TEST_PACKAGE = "com.example.androidcookbook.fixture"


@pytest.fixture
def android_serial() -> str:

    devices = [device for device in list_devices() if device.state == "device"]

    if not devices:
        pytest.skip("No Android device avaiable")

    return devices[0].serial


@pytest.fixture
def test_apk() -> Path:

    project_root = Path(__file__).resolve().parents[2]

    apk = project_root / "tests" / "fixtures" / "test_app" / "cookbook-test-app.apk"

    if not apk.exists():
        pytest.skip(f"Test APK not found: {apk}")

    return apk


@pytest.fixture
def clean_test_package(android_serial: str):

    #
    # Setup
    #
    if package_exists(android_serial, TEST_PACKAGE):

        uninstall_package(android_serial, TEST_PACKAGE)

    yield TEST_PACKAGE

    #
    # Teardown
    #
    if package_exists(android_serial, TEST_PACKAGE):

        uninstall_package(android_serial, TEST_PACKAGE)

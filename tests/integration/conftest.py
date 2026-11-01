import os
import subprocess
from pathlib import Path

import pytest

from android_cookbook.activity_manager import (
    force_stop_package,
)
from android_cookbook.package_manager import (
    package_exists,
    uninstall_package,
)
from android_cookbook.activity_recreation import(
    capture_rotation_settings,
    restore_rotation_settings,
    set_user_rotation,
)

TEST_PACKAGE = "com.example.androidcookbook.fixture"


@pytest.fixture(scope="session")
def android_serial() -> str:

    serial = os.environ.get("ANDROID_SERIAL", "").strip()

    if not serial:
        pytest.skip(
            "Set ANDROID_SERIAL to dedicated emulator. exec 'export ANDROID_SERIAL=emulator-5554'"
        )

    if not serial.startswith("emulator-"):
        pytest.skip("Descructive tests require an emulator serial.")

    result = subprocess.run(
        [
            "adb",
            "-s",
            serial,
            "get-state",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0 or result.stdout.strip() != "device":
        pytest.skip(f"Android emulator {serial} is not ready.")

    return serial


@pytest.fixture(scope="session")
def test_apk() -> Path:

    project_root = Path(__file__).resolve().parents[2]

    apk = project_root / "tests" / "fixtures" / "test-app" / "cookbook-test-app.apk"

    if not apk.exists():
        pytest.skip("Test APK not found. " "Run ./scripts/build-test-apk.sh first.")

    return apk


@pytest.fixture
def clean_test_package(android_serial: str):

    #
    # Setup
    #

    if package_exists(android_serial, TEST_PACKAGE):
        pytest.fail(
            "Fixutre package is already installed. "
            "Remove it manually before running destructive tests."
            f"Run 'adb -s {android_serial} shell pm uninstall {TEST_PACKAGE}'"  # uninstall_package(android_serial, TEST_PACKAGE
        )

    try:

        yield TEST_PACKAGE

    finally:

        #
        # Teardown
        #

        try:

            force_stop_package(android_serial, TEST_PACKAGE)

        finally:

            if package_exists(android_serial, TEST_PACKAGE):
                result = uninstall_package(
                    android_serial,
                    TEST_PACKAGE,
                )

                if "Success" not in result:
                    pytest.fail(f"Fixture cleanup failed: {result}")

@pytest.fixture
def controlled_rotation(android_serial):
    original = capture_rotation_settings(android_serial)

    try:
        set_user_rotation(android_serial, 0)
        yield
    finally:
        restore_rotation_settings(
            android_serial,
            original,
        )
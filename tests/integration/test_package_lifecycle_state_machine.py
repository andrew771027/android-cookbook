from enum import Enum, auto
from pathlib import Path

import pytest
from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from android_cookbook.adb import list_devices
from android_cookbook.package_manager import (
    clear_package,
    disable_package_for_user,
    enable_package,
    install_apk,
    list_packages,
    package_exists,
    uninstall_package,
)

PACKAGE_NAME = "com.example.androidcookbook.fixture"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APK_PATH = PROJECT_ROOT / "tests" / "fixtures" / "test_app" / "cookbook-test-app.apk"


class PackageState(Enum):
    NOT_INSTALLED = auto()
    ENABLED = auto()
    DISABLED = auto()


@settings(max_examples=3, stateful_step_count=5, deadline=None)
class AndroidPackageLifecycleStateMachine(RuleBasedStateMachine):
    """Exercise package installation and enabled state on the first online device.

    Each example removes the disposable fixture package before and after its rules.
    The APK must use PACKAGE_NAME. Enabled state does not describe process state.
    """

    def __init__(self):
        super().__init__()
        self.package_name = PACKAGE_NAME
        self.apk_path = APK_PATH
        self.state = PackageState.NOT_INSTALLED

        self._check_apk_available()

        self.serial = self._android_serial()

        self._reset_device_state()

    def _android_serial(self) -> str:
        devices = [device for device in list_devices() if device.state == "device"]

        if not devices:
            pytest.skip("No Android device available")

        return devices[0].serial

    def _check_apk_available(self):
        # Validate the fixture before connecting to or changing the device.
        if not self.apk_path.is_file() or self.apk_path.stat().st_size == 0:
            pytest.skip(f"A valid, non-empty test APK is required: {self.apk_path}")

    def _reset_device_state(self):
        if package_exists(self.serial, self.package_name):
            uninstall_package(self.serial, self.package_name)
        assert not package_exists(self.serial, self.package_name)
        self.state = PackageState.NOT_INSTALLED

    @precondition(lambda self: self.state == PackageState.NOT_INSTALLED)
    @rule()
    def install(self):
        assert install_apk(self.serial, self.apk_path).strip() == "Success"
        assert package_exists(self.serial, self.package_name)
        # Establish enabled state explicitly instead of assuming the APK default.
        enable_package(self.serial, self.package_name)
        self.state = PackageState.ENABLED

    @precondition(lambda self: self.state == PackageState.DISABLED)
    @rule()
    def enable(self):
        enable_package(self.serial, self.package_name)
        self.state = PackageState.ENABLED

    @precondition(lambda self: self.state == PackageState.ENABLED)
    @rule()
    def disable(self):
        disable_package_for_user(self.serial, self.package_name, user_id=0)
        self.state = PackageState.DISABLED

    @precondition(lambda self: self.state != PackageState.NOT_INSTALLED)
    @rule()
    def clear_data(self):
        assert clear_package(self.serial, self.package_name)
        assert package_exists(self.serial, self.package_name)
        # Clearing data preserves enabled/disabled state in this model.

    @precondition(lambda self: self.state != PackageState.NOT_INSTALLED)
    @rule()
    def uninstall(self):
        assert uninstall_package(self.serial, self.package_name).strip() == "Success"
        assert not package_exists(self.serial, self.package_name)
        self.state = PackageState.NOT_INSTALLED

    @invariant()
    def package_presence_matches_model(self):
        assert package_exists(self.serial, self.package_name) == (
            self.state != PackageState.NOT_INSTALLED
        )

    @invariant()
    def enabled_state_matches_model(self):
        if self.state == PackageState.NOT_INSTALLED:
            return
        enabled = list_packages(self.serial, enabled_only=True, filter_text=self.package_name)
        disabled = list_packages(self.serial, disabled_only=True, filter_text=self.package_name)
        assert any(package.name == self.package_name for package in enabled) == (
            self.state == PackageState.ENABLED
        )
        assert any(package.name == self.package_name for package in disabled) == (
            self.state == PackageState.DISABLED
        )

    def teardown(self):
        self._reset_device_state()


TestAndroidPackageLifecycleStateMachine = AndroidPackageLifecycleStateMachine.TestCase
TestAndroidPackageLifecycleStateMachine = pytest.mark.integration(
    TestAndroidPackageLifecycleStateMachine
)
TestAndroidPackageLifecycleStateMachine = pytest.mark.destructive(
    TestAndroidPackageLifecycleStateMachine
)

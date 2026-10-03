from enum import Enum, auto
from pathlib import Path

from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from android_cookbook.package_manager import PackageInfo


class PackageState(Enum):
    NOT_INSTALLED = auto()
    ENABLED = auto()
    DISABLED = auto()


class FakePackageManager:
    """In-memory fixture with the package_manager function signatures.

    This fake models one third-party package on one device for user 0.
    Enabled state is independent of process state.
    """

    def __init__(self, package_name: str):
        self.package_name = package_name
        self.installed = False
        self.enabled = False

    def install_apk(
        self,
        serial: str,
        apk_path: str | Path,
        *,
        replace: bool = False,
        grant_permissions: bool = False,
    ) -> str:
        if self.installed and not replace:
            return "Failure [INSTALL_FAILED_ALREADY_EXISTS]"

        if not self.installed:
            self.enabled = True
        self.installed = True
        return "Success"

    def uninstall_package(
        self,
        serial: str,
        package_name: str,
        *,
        keep_data: bool = False,
    ) -> str:
        if not self.package_exists(serial, package_name):
            return "Failure [DELETE_FAILED_INTERNAL_ERROR]"

        self.installed = False
        self.enabled = False
        return "Success"

    def enable_package(self, serial: str, package_name: str) -> str:
        if not self.package_exists(serial, package_name):
            raise RuntimeError("package is not installed")

        self.enabled = True
        return f"Package {package_name} new state: enabled"

    def disable_package_for_user(self, serial: str, package_name: str, user_id: int = 0) -> str:
        if user_id != 0:
            raise ValueError("the fake only models user 0")
        if not self.package_exists(serial, package_name):
            raise RuntimeError("package is not installed")

        self.enabled = False
        return f"Package {package_name} new state: disabled-user"

    def clear_package(self, serial: str, package_name: str) -> bool:
        # Clearing data preserves the package's enabled/disabled state.
        return self.package_exists(serial, package_name)

    def package_exists(self, serial: str, package_name: str) -> bool:
        return any(
            package.name == package_name
            for package in self.list_packages(serial, filter_text=package_name)
        )

    def list_packages(
        self,
        serial: str,
        *,
        system_only: bool = False,
        third_party_only: bool = False,
        enabled_only: bool = False,
        disabled_only: bool = False,
        filter_text: str | None = None,
    ) -> list[PackageInfo]:
        if system_only and third_party_only:
            raise ValueError("system_only and third_party_only cannot both be True")
        if enabled_only and disabled_only:
            raise ValueError("enabled_only and disabled_only cannot both be True")

        if not self.installed or system_only:
            return []
        if enabled_only and not self.enabled:
            return []
        if disabled_only and self.enabled:
            return []
        if filter_text and filter_text not in self.package_name:
            return []
        return [PackageInfo(name=self.package_name)]


@settings(max_examples=100, stateful_step_count=30, deadline=None)
class PackageLifecycleStateMachine(RuleBasedStateMachine):
    """Model the same package operations as the integration state machine.

    install: NOT_INSTALLED -> ENABLED
    disable: ENABLED -> DISABLED
    enable: DISABLED -> ENABLED
    clear_data: preserve either installed state
    uninstall: either installed state -> NOT_INSTALLED
    """

    def __init__(self):
        super().__init__()
        self.serial = "emulator-5554"
        self.package_name = "com.example.cookbook"
        self.apk_path = "fake-test-app.apk"
        self.package_manager = FakePackageManager(self.package_name)
        self.state = PackageState.NOT_INSTALLED

    @precondition(lambda self: self.state == PackageState.NOT_INSTALLED)
    @rule()
    def install(self):
        assert self.package_manager.install_apk(self.serial, self.apk_path) == "Success"
        assert self.package_manager.package_exists(self.serial, self.package_name)
        self.package_manager.enable_package(self.serial, self.package_name)
        self.state = PackageState.ENABLED

    @precondition(lambda self: self.state == PackageState.DISABLED)
    @rule()
    def enable(self):
        self.package_manager.enable_package(self.serial, self.package_name)
        self.state = PackageState.ENABLED

    @precondition(lambda self: self.state == PackageState.ENABLED)
    @rule()
    def disable(self):
        self.package_manager.disable_package_for_user(self.serial, self.package_name, user_id=0)
        self.state = PackageState.DISABLED

    @precondition(lambda self: self.state != PackageState.NOT_INSTALLED)
    @rule()
    def clear_data(self):
        assert self.package_manager.clear_package(self.serial, self.package_name)
        assert self.package_manager.package_exists(self.serial, self.package_name)

    @precondition(lambda self: self.state != PackageState.NOT_INSTALLED)
    @rule()
    def uninstall(self):
        assert (
            self.package_manager.uninstall_package(self.serial, self.package_name).strip()
            == "Success"
        )
        assert not self.package_manager.package_exists(self.serial, self.package_name)
        self.state = PackageState.NOT_INSTALLED

    @invariant()
    def package_presence_matches_model(self):
        assert self.package_manager.package_exists(self.serial, self.package_name) == (
            self.state != PackageState.NOT_INSTALLED
        )

    @invariant()
    def enabled_state_matches_model(self):
        enabled = self.package_manager.list_packages(
            self.serial, enabled_only=True, filter_text=self.package_name
        )
        disabled = self.package_manager.list_packages(
            self.serial, disabled_only=True, filter_text=self.package_name
        )
        assert any(package.name == self.package_name for package in enabled) == (
            self.state == PackageState.ENABLED
        )
        assert any(package.name == self.package_name for package in disabled) == (
            self.state == PackageState.DISABLED
        )


TestPackageLifecycleStateMachine = PackageLifecycleStateMachine.TestCase

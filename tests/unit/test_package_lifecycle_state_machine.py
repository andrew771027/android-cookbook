from enum import Enum, auto
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest
from hypothesis import settings
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    precondition,
    rule,
)

import android_cookbook.adb as adb_module
import android_cookbook.package_manager as package_manager


class PackageState(Enum):
    NOT_INSTALLED = auto()
    ENABLED = auto()
    DISABLED = auto()


@settings(max_examples=100, stateful_step_count=30, deadline=None)
class PackageLifecycleStateMachine(RuleBasedStateMachine):
    """
    Stateful unit test for Android package lifecycle.

    Production code under test:

        package_manager.py
                ↓
            shell.py
                ↓
             adb.py
                ↓
        subprocess.run()
                ↓
        monkeypatched response

    Expected model state:
        self.state

    Simulated Android state:
        self.android_installed
        self.android_enabled

    These two states are intentionally independent.
    """

    def __init__(self):
        super().__init__()
        self.serial = "emulator-5554"
        self.package_name = "com.example.cookbook.fixture"

        # =====================================================
        # Hypothesis expected/model state
        # =====================================================
        self.state = PackageState.NOT_INSTALLED

        # =====================================================
        # Simulated Android actual state
        #
        # Important:
        # Do NOT derive these values from self.state.
        #
        # They are changed only when production code generates
        # the correct ADB command.
        # =====================================================
        self.android_installed = False
        self.android_enabled = False

        # Optional command history for debugging.
        self.command_history: list[list[str]] = []
        self.response_history: list[str] = []

        # =====================================================
        # install_apk() checks Path.exists().
        #
        # Create a real temporary file so the production
        # FileNotFoundError logic is still exercised normally.
        # =====================================================
        self.temp_dir = TemporaryDirectory()

        self.apk_path = Path(self.temp_dir.name) / "cookbook-test-app.apk"
        self.apk_path.write_bytes(b"fake apk content")

        # =====================================================
        # Patch only the system/process boundary.
        # =====================================================
        self.monkeypatch = pytest.MonkeyPatch()

        self.monkeypatch.setattr(
            adb_module.subprocess,
            "run",
            self._fake_subprocess_run,
        )

    # =========================================================
    # Fake subprocess / simulated Android
    # =========================================================
    def _fake_subprocess_run(
        self,
        command,
        *,
        capture_output=False,
        text=False,
        check=False,
        **kwargs,
    ):
        """
        Replacement for subprocess.run() inside adb.py.

        The real production chain still executes:

            package_manager
                -> shell
                -> adb
                -> subprocess.run

        Only subprocess.run is replaced.
        """

        command = list(command)

        self.command_history.append(command)

        output = self._fake_android_response(command)

        self.response_history.append(output)

        return SimpleNamespace(
            args=command,
            returncode=0,
            stdout=output,
            stderr="",
        )

    def _fake_android_response(
        self,
        command: list[str],
    ):
        """
        Simulate a very small subset of Android/ADB behavior.

        Supported commands:

            adb -s SERIAL install ...
            adb -s SERIAL uninstall ...
            adb -s SERIAL shell pm list packages ...
            adb -s SERIAL shell pm clear ...
            adb -s SERIAL shell pm enable ...
            adb -s SERIAL shell pm disable-user ...
        """

        assert command
        assert command[0] == "adb"

        adb_args = command[1:]

        # -----------------------------------------------------
        # adb -s SERIAL install APK
        # -----------------------------------------------------
        if "install" in adb_args:
            return self._fake_install(adb_args)

        # -----------------------------------------------------
        # adb -s SERIAL uninstall PACKAGE
        # -----------------------------------------------------
        if "uninstall" in adb_args:
            return self._fake_uninstall(adb_args)

        # -----------------------------------------------------
        # adb -s SERIAL shell ...
        # -----------------------------------------------------
        if "shell" in adb_args:
            shell_index = adb_args.index("shell")

            shell_command = adb_args[shell_index + 1 :]

            return self._fake_shell_response(shell_command)

        raise AssertionError(f"Unexpected ADB command: {command}")

    def _fake_install(
        self,
        command: list[str],
    ) -> str:
        """
        Simulate:

            adb -s SERIAL install APK
        """
        assert "install" in command

        if self.android_installed:
            return "Failure [INSTALL_FAILED_ALREADY_EXISTS]"

        self.android_installed = True

        # Fresh installation defaults to enabled
        # in this simplified model.
        self.android_enabled = True

        return "Success"

    def _fake_uninstall(self, command: list[str]) -> str:
        """
        Simulate:

            adb -s SERIAL uninstall PACKAGE
        """
        assert "uninstall" in command

        if not self.android_installed:
            return "Failure [DELETE_FAILED_INTERNAL_ERROR]"

        self.android_installed = False
        self.android_enabled = False

        return "Success"

    def _fake_shell_response(
        self,
        command: list[str],
    ) -> str:
        """
        Simulate Android shell package-manager commands.
        """

        if command[:3] == [
            "pm",
            "list",
            "packages",
        ]:
            return self._fake_list_packages(command)

        if len(command) >= 3 and command[0] == "pm" and command[1] == "clear":
            return self._fake_clear_package(command)

        if len(command) >= 3 and command[0] == "pm" and command[1] == "enable":
            return self._fake_enable_package(command)

        if len(command) >= 5 and command[0] == "pm" and command[1] == "disable-user":
            return self._fake_disable_package(command)

        raise AssertionError(f"Unexpected shell command: {command}")

    def _fake_list_packages(
        self,
        command: list[str],
    ) -> str:
        """
        Simulate:

            pm list packages
            pm list packages -e
            pm list packages -d
            pm list packages -s
            pm list packages -3
            pm list packages FILTER
        """
        if not self.android_installed:
            return ""

        # Our fixture package is third-party.
        if "-s" in command:
            return ""

        if "-e" in command and not self.android_enabled:
            return ""

        if "-d" in command and self.android_enabled:
            return ""

        package_filter = self._extract_package_filter(command)

        if package_filter is not None and package_filter not in self.package_name:
            return ""

        return f"package:{self.package_name}"

    def _fake_clear_package(
        self,
        command: list[str],
    ) -> str:
        """
        Simulate:

            pm clear PACKAGE

        clear_data preserves ENABLED / DISABLED state
        in this model.
        """
        assert command[0] == "pm"
        assert command[1] == "clear"

        package_name = command[2]

        assert package_name == self.package_name, f"Unexpected package: {package_name}"

        if not self.android_installed:
            return "Falsed"
        return "Success"

    def _fake_enable_package(
        self,
        command: list[str],
    ) -> str:
        """
        Simulate:

            pm enable PACKAGE
        """

        self._require_android_package()

        self.android_enabled = True

        return f"Package {self.package_name} new state: enabled"

    def _fake_disable_package(
        self,
        command: list[str],
    ) -> str:
        """
        Simulate:

            pm disable-user --user 0 PACKAGE
        """
        self._require_android_package()

        self.android_enabled = False

        return f"Package {self.package_name} new state: disabled-user"

    def _require_android_package(self):
        if not self.android_installed:
            raise AssertionError(
                "Package-manager operation was attempted while package was not installed"
            )

    @staticmethod
    def _extract_package_filter(
        command: list[str],
    ) -> str | None:
        """
        Example:

            pm list packages -e com.example.app

        Returns:

            com.example.app
        """
        try:
            package_index = command.index("pacakges")
        except ValueError:
            return None

        remaining = command[package_index + 1 :]

        non_option_values = [value for value in remaining if not value.startswith("-")]

        if not non_option_values:
            return None

        return non_option_values[-1]

    # =========================================================
    # Hypothesis rules
    # =========================================================

    @precondition(lambda self: self.state == PackageState.NOT_INSTALLED)
    @rule()
    def install(self):
        result = package_manager.install_apk(
            self.serial,
            self.apk_path,
            replace=True,
            allow_test_packages=True,
        )

        assert result == "Success"

        assert package_manager.package_exists(self.serial, self.package_name)

        # Establish enabled state explicitly,
        # matching the integration test.
        enabled_result = package_manager.enable_package(self.serial, self.package_name)

        assert "enabled" in enabled_result

        self.state = PackageState.ENABLED

    @precondition(lambda self: self.state == PackageState.DISABLED)
    @rule()
    def enable(self):
        result = package_manager.enable_package(
            self.serial,
            self.package_name,
        )

        assert "enabled" in result

        self.state = PackageState.ENABLED

    @precondition(lambda self: self.state == PackageState.ENABLED)
    @rule()
    def disable(self):
        result = package_manager.disable_package_for_user(
            self.serial,
            self.package_name,
            user_id=0,
        )

        assert "disabled-user" in result

        self.state = PackageState.DISABLED

    @precondition(lambda self: self.state != PackageState.NOT_INSTALLED)
    @rule()
    def clear_data(self):
        result = package_manager.clear_package(
            self.serial,
            self.package_name,
        )

        assert result is True

        result = package_manager.package_exists(
            self.serial,
            self.package_name,
        )

        # Do NOT change self.state.
        #
        # ENABLED  -> ENABLED
        # DISABLED -> DISABLED

    @precondition(lambda self: self.state != PackageState.NOT_INSTALLED)
    @rule()
    def uninstall(self):
        result = package_manager.uninstall_package(
            self.serial,
            self.package_name,
        )

        assert result == "Success"

        assert not package_manager.package_exists(
            self.serial,
            self.package_name,
        )

        self.state = PackageState.NOT_INSTALLED

    # =========================================================
    # Invariants
    # =========================================================
    @invariant()
    def package_presence_matches_model(self):
        actual_result = package_manager.package_exists(
            self.serial,
            self.package_name,
        )

        expected_result = self.state != PackageState.NOT_INSTALLED

        assert actual_result == expected_result

    @invariant()
    def enabled_state_matches_model(self):
        enabled_packages = package_manager.list_packages(
            self.serial,
            enabled_only=True,
            filter_text=self.package_name,
        )
        disabled_packages = package_manager.list_packages(
            self.serial,
            disabled_only=True,
            filter_text=self.package_name,
        )

        actual_enabled = any(package.name == self.package_name for package in enabled_packages)

        actual_disabled = any(package.name == self.package_name for package in disabled_packages)

        expected_enabled = self.state == PackageState.ENABLED

        expected_disabled = self.state == PackageState.DISABLED

        assert actual_enabled == expected_enabled

        assert actual_disabled == expected_disabled

    # =========================================================
    # Cleanup
    # =========================================================
    def teardown(self):
        self.monkeypatch.undo()

        self.temp_dir.cleanup()


TestPackageLifecycleStateMachine = PackageLifecycleStateMachine.TestCase

import pytest

from android_cookbook.package_manager import (
    PackageInfo,
    PackagePath,
    clear_package,
    get_package_path,
    install_apk,
    list_packages,
    package_exists,
    parse_package_line,
    parse_package_list,
    parse_package_paths,
    uninstall_package,
)
from android_cookbook.shell import ShellResult


def test_parse_package_line():

    actual = parse_package_line("package:com.android.settings")

    assert actual == PackageInfo(name="com.android.settings")


def test_parse_package_line_returns_none_for_invalid_line():

    actual = parse_package_line("invalid")

    assert actual is None


def test_parse_package_line_returns_none_for_empty_package():

    actual = parse_package_line("package:")

    assert actual is None


def test_parse_package_list():

    output = """
    package:com.android.settings
    package:com.android.systemui
    package:com.google.android.gms
"""

    actual = parse_package_list(output)

    assert actual == [
        PackageInfo(name="com.android.settings"),
        PackageInfo(name="com.android.systemui"),
        PackageInfo(name="com.google.android.gms"),
    ]


def test_list_packages(monkeypatch):

    captured_args = None

    def fake_run_shell(
        serial,
        *command,
    ):

        nonlocal captured_args

        captured_args = (
            serial,
            command,
        )

        return ShellResult(
            command="pm list packages",
            output=("package:com.example.one\n" "package:com.example.two\n"),
        )

    monkeypatch.setattr("android_cookbook.package_manager.run_shell", fake_run_shell)

    actual = list_packages("emulator-5554")

    assert actual == [
        PackageInfo(name="com.example.one"),
        PackageInfo(name="com.example.two"),
    ]

    assert captured_args == (
        "emulator-5554",
        (
            "pm",
            "list",
            "packages",
        ),
    )


def test_list_system_packages(monkeypatch):

    captured_command = None

    def fake_run_shell(
        serial,
        *command,
    ):

        nonlocal captured_command

        captured_command = command

        return ShellResult(
            command="",
            output="package:com.android.settings\n",
        )

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_shell",
        fake_run_shell,
    )

    list_packages(
        "emulator-5554",
        system_only=True,
    )

    assert captured_command == (
        "pm",
        "list",
        "packages",
        "-s",
    )


def test_list_third_party_packages(monkeypatch):

    captured_command = None

    def fake_run_shell(
        serial,
        *command,
    ):

        nonlocal captured_command

        captured_command = command

        return ShellResult(
            command="",
            output="package:com.example.app\n",
        )

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_shell",
        fake_run_shell,
    )

    list_packages(
        "emulator-5554",
        third_party_only=True,
    )

    assert captured_command == (
        "pm",
        "list",
        "packages",
        "-3",
    )


def test_system_and_third_party_cannot_both_be_enabled():

    with pytest.raises(
        ValueError,
        match="cannot both be True",
    ):

        list_packages(
            "emulator-5554",
            system_only=True,
            third_party_only=True,
        )


def test_enabled_and_disabled_cannot_both_be_enabled():

    with pytest.raises(
        ValueError,
        match="cannot both be True",
    ):

        list_packages(
            "emulator-5554",
            enabled_only=True,
            disabled_only=True,
        )


def test_package_exists(monkeypatch):

    def fake_list_packages(
        serial,
        **kwargs,
    ):

        return [PackageInfo(name="com.android.settings")]

    monkeypatch.setattr(
        "android_cookbook.package_manager.list_packages",
        fake_list_packages,
    )

    assert package_exists(
        "emulator-5554",
        "com.android.settings",
    )


def test_package_does_not_exists(monkeypatch):

    def fake_list_packages(
        serial,
        **kwargs,
    ):

        return []

    monkeypatch.setattr(
        "android_cookbook.package_manager.list_packages",
        fake_list_packages,
    )

    assert not package_exists(
        "emulator-5554",
        "com.example.missing",
    )


def test_parse_single_package_path():

    output = (
        "package:/system/priv-app/",
        "Settings/Settings.apk\n",
    )

    actual = parse_package_paths(
        "com.android.settings",
        output,
    )

    assert actual == PackagePath(
        package_name="com.android.settings",
        path=[
            "/system/priv-app/",
            "Settings/Settings.apk",
        ],
    )


def test_parse_multiple_package_paths():

    output = """
    package:/data/app/example/base.apk
    package:/data/app/example/split_config.en.apk
    package:/data/app/example/split_config.xxhdpi.apk
"""

    actual = parse_package_paths(
        "com.example.app",
        output,
    )

    assert actual == PackagePath(
        package_name="com.example.app",
        paths=[
            "/data/app/example/base.apk",
            "/data/app/example/split_config.en.ap",
            "/data/app/example/split_config.xxhdpi.apk",
        ],
    )


def test_get_pacakge_path(monkeypatch):

    captured_command = None

    def fake_run_shell(
        serial,
        *command,
    ):

        nonlocal captured_command

        captured_command = command

        return ShellResult(
            command="",
            output=("package:/system/app/" "Example/Example.apk\n"),
        )

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_shell",
        fake_run_shell,
    )

    actual = get_package_path(
        "emulator-5554",
        "com.example.app",
    )

    assert actual.paths == ["/system/app/Example/Example.apk"]

    assert captured_command == (
        "pm",
        "path",
        "com.example.app",
    )


def test_clear_package_success(monkeypatch):

    def fake_run_shell(
        serial,
        *command,
    ):
        return ShellResult(
            command="",
            output="Success\n",
        )

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_shell",
        fake_run_shell,
    )

    assert clear_package(
        "emulator-5554",
        "com.example.app",
    )


def test_clear_package_failure(monkeypatch):

    def fake_run_shell(
        serial,
        *command,
    ):

        return ShellResult(
            command="",
            output="Failed\n",
        )

    monkeypatch.setattr("android_cookbook.package_manager.run_shell", fake_run_shell),

    assert not clear_package(
        "emulator-5554",
        "com.example.app",
    )


def test_install_apk(
    monkeypatch,
    tmp_path,
):

    apk = tmp_path / "example.apk"

    apk.write_bytes(b"fake apk")

    captured_args = None

    def fake_run_adb(*args):

        nonlocal captured_args

        captured_args = args

        return "Success"

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_adb",
        fake_run_adb,
    )

    actual = install_apk(
        "emulator-5554",
        apk,
    )

    assert actual == "Success"

    assert captured_args == (
        "-s",
        "emulator-5554",
        "install",
        str(apk),
    )


def test_install_apk_with_options(monkeypatch, tmp_path):

    apk = tmp_path / "example.apk"

    apk.write_bytes(b"fake")

    captured_args = None

    def fake_run_adb(*args):

        nonlocal captured_args

        captured_args = args

        return "Success"

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_adb",
        fake_run_adb,
    )

    install_apk(
        "emulator-5554",
        apk,
        replace=True,
        grant_permissions=True,
    )

    assert captured_args == (
        "-s",
        "emulator-5554",
        "install",
        "-r",
        "-g",
        str(apk),
    )


def test_install_missing_apk():

    with pytest.raises(FileNotFoundError):

        install_apk(
            "emulator-5554",
            "missing.apk",
        )


def test_uninstall_package(monkeypatch):

    captured_args = None

    def fake_run_adb(*args):

        nonlocal captured_args

        captured_args = args

        return "Success"

    monkeypatch.setattr(
        "android_cookbook.package_manager.run_adb",
        fake_run_adb,
    )

    actual = uninstall_package(
        "emulator-5554",
        "com.example.app",
    )

    assert actual == "Success"

    assert captured_args == (
        "-s",
        "emulator-5554",
        "uninstall",
        "com.example.app",
    )

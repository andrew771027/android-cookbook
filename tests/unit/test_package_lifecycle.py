from android_cookbook.package_lifecycle import (
    PackageLifecycleResult,
    run_package_lifecycle,
)
from android_cookbook.package_manager import PackagePath


def test_run_package_lifecycle(
    monkeypatch,
    tmp_path,
):

    apk = tmp_path / "test.apk"

    apk.write_bytes(b"fake")

    package_name = "com.example.test"

    package_states = iter([True, True, False])

    def fake_install(
        serial,
        apk_path,
        **kwargs,
    ):

        return "Success"

    def fake_exists(
        serial,
        pacakge,
    ):

        return next(package_states)

    def fake_get_path(
        serial,
        package,
    ):

        return PackagePath(
            package_name=package,
            paths=["/data/app/test/base.apk"],
        )

    def fake_clear(
        serial,
        package,
    ):

        return True

    def fake_uninstall(
        serial,
        package,
        **kwargs,
    ):

        return "Success"

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.install_apk",
        fake_install,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.package_exists",
        fake_exists,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.get_package_path",
        fake_get_path,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.clear_package",
        fake_clear,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.uninstall_package",
        fake_uninstall,
    )

    actual = run_package_lifecycle(
        "emulator-5554",
        apk,
        package_name,
    )

    assert actual == PackageLifecycleResult(
        package_name=package_name,
        installed=True,
        apk_paths=["/data/app/test/base.apk"],
        cleared=True,
        still_installed_after_clear=True,
        uninstalled=True,
        removed=True,
    )


def test_package_lifecycle_operation_order(
    monkeypatch,
    tmp_path,
):

    apk = tmp_path / "test.apk"
    apk.write_bytes(b"fake")

    calls = []

    states = iter([True, True, False])

    def fake_install(
        serial,
        apk_path,
        **kwargs,
    ):
        calls.append("install")
        return "Success"

    def fake_exists(
        serial,
        pacakge,
    ):
        calls.append("exists")
        return next(states)

    def fake_path(
        serial,
        package,
    ):
        calls.append("path")
        return PackagePath(
            package_name=package,
            paths=["/data/app/test/base.apk"],
        )

    def fake_clear(
        serial,
        package,
    ):
        calls.append("clear")
        return True

    def fake_uninstall(
        serial,
        package,
        **kwargs,
    ):
        calls.append("uninstall")
        return "Success"

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.install_apk",
        fake_install,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.package_exists",
        fake_exists,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.get_package_path",
        fake_path,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.clear_package",
        fake_clear,
    )

    monkeypatch.setattr(
        "android_cookbook.package_lifecycle.uninstall_package",
        fake_uninstall,
    )

    run_package_lifecycle(
        "emulator-5554",
        apk,
        "com.example.test",
    )

    assert calls == [
        "install",
        "exists",
        "path",
        "clear",
        "exists",
        "uninstall",
        "exists",
    ]

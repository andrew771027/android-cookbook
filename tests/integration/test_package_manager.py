import pytest

from android_cookbook.package_manager import (
    get_package_path,
    list_packages,
    package_exists,
)

pytestmark = pytest.mark.integration


def test_package_manager_returns_package(android_serial):

    packages = list_packages(android_serial)

    assert packages


def test_android_settings_package_exists(android_serial):

    assert package_exists(
        android_serial,
        "com.android.settings",
    )


def test_settings_package_has_apk_path(android_serial):

    result = get_package_path(
        android_serial,
        "com.android.settings",
    )

    assert result.paths

    assert any(path.endswith(".apk") for path in result.paths)


def test_system_packages_are_available(android_serial):

    packages = list_packages(
        android_serial,
        system_only=True,
    )

    assert packages

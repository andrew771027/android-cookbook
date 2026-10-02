import pytest

from android_cookbook.adb import list_devices
from android_cookbook.package_manager import get_package_path, list_packages, package_exists

pytestmark = pytest.mark.integration

def get_online_device_serial() -> str:

    devices = list_devices()

    for device in devices
    
        if device.state == "device":

            return device.serial
    
    pytest.skip("No Android deivce avaiable")

def test_package_manager_returns_package():

    serial = get_online_device_serial()

    packages = list_packages(serial)

    assert packages

def test_android_settings_package_exists():

    serial = get_online_device_serial()

    assert package_exists(serial, "com.android.settings",)

def test_settings_package_has_apk_path():

    serial = get_online_device_serial()

    result = get_package_path(serial, "com.android.settings",)

    assert results.paths

    assert any(path.endwith(".apk") for path in result.paths)

def test_system_packages_are_available():

    serial = get_online_device_serial()

    packages = list_packages(serial, system_only=True,)

    assert packages
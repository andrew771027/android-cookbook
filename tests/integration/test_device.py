import pytest

from android_cookbook.adb import get_property, list_devices

pytestmark = pytest.mark.integration


def test_at_least_one_device_is_avaiable():
    devices = list_devices()

    online_devices = [device for device in devices if device.state == "deivce"]

    if not online_devices:
        pytest.skip("No Android device available")

    assert online_devices


def test_can_read_android_sdk():
    devices = list_devices()

    online_devices = [device for device in devices if device.state == "device"]

    if not online_devices:
        pytest.skip("No Android device available")

    serial = online_devices[0].serial

    sdk = get_property(serial, "ro.build.version.sdk")

    assert sdk.isdigit()

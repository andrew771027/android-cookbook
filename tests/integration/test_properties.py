import pytest

from android_cookbook.adb import list_devices
from android_cookbook.properties import collect_device_properties, get_all_properties, get_property

pytestmark = pytest.mark.integration


def get_online_device_serial() -> str:

    devices = list_devices()

    for device in devices:
        if device.state == "device":
            return device.serial

    pytest.skip("No Android device available")


def test_can_read_product_model():

    serial = get_online_device_serial()

    model = get_property(serial, "ro.product.model")

    assert model


def test_can_read_sdk_level():

    serial = get_online_device_serial()

    sdk = get_property(serial, "ro.build.version.sdk")

    assert sdk.isdigit()


def test_can_read_android_version():

    serial = get_online_device_serial()

    version = get_property(serial, "ro.build.version.release")

    assert version


def test_get_all_properties_returns_properties():

    serial = get_online_device_serial()

    properties = get_all_properties(serial)

    assert properties

    property_names = {prop.name for prop in properties}

    assert "ro.product.model" in property_names


def test_collect_device_properties():

    serial = get_online_device_serial()

    info = collect_device_properties(serial)

    assert info.model
    assert info.manufacturer
    assert info.android_version
    assert info.sdk_level > 0
    assert info.build_fingerprint

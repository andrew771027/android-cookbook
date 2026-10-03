import pytest

from android_cookbook.properties import (
    collect_device_properties,
    get_all_properties,
    get_property,
)

pytestmark = pytest.mark.integration


def test_can_read_product_model(android_serial):

    model = get_property(android_serial, "ro.product.model")

    assert model


def test_can_read_sdk_level(android_serial):

    sdk = get_property(android_serial, "ro.build.version.sdk")

    assert sdk.isdigit()


def test_can_read_android_version(android_serial):

    version = get_property(android_serial, "ro.build.version.release")

    assert version


def test_get_all_properties_returns_properties(android_serial):

    properties = get_all_properties(android_serial)

    assert properties

    property_names = {prop.name for prop in properties}

    assert "ro.product.model" in property_names


def test_collect_device_properties(android_serial):

    info = collect_device_properties(android_serial)

    assert info.model
    assert info.manufacturer
    assert info.android_version
    assert info.sdk_level > 0
    assert info.build_fingerprint

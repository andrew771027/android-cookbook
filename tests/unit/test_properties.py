from android_cookbook.properties import (
    AndroidProperty,
    DeviceProperties,
    collect_device_properties,
    get_all_properties,
    get_property,
    parse_properties,
    parse_property_line,
)
from android_cookbook.shell import ShellResult


def test_parse_property_line():

    line = "[ro.product.model]: [Pixel 10]"

    actual = parse_property_line(line)

    assert actual == AndroidProperty(name="ro.product.model", value="Pixel 10")


def test_parse_property_line_with_empty_value():

    line = "[some.property]: []"

    actual = parse_property_line(line)

    assert actual == AndroidProperty(name="some.property", value="")


def test_parse_property_line_returns_none_for_invalid_line():

    actual = parse_property_line("invalid property line")

    assert actual is None


def test_parse_properties():

    output = """
    [ro.product.model]: [Pixel 10]
    [ro.build.version.release]: [16]
    [ro.build.version.sdk]: [36]
    """

    actual = parse_properties(output)

    assert actual == [
        AndroidProperty(name="ro.product.model", value="Pixel 10"),
        AndroidProperty(name="ro.build.version.release", value="16"),
        AndroidProperty(name="ro.build.version.sdk", value="36"),
    ]


def test_get_property(monkeypatch):

    captured_args = None

    def fake_run_shell(serial, *command):

        nonlocal captured_args

        captured_args = (serial, command)

        return ShellResult(command="getprop ro.product.model", output="Pixel 10\n")

    monkeypatch.setattr("android_cookbook.properties.run_shell", fake_run_shell)

    actual = get_property(serial="ABC123", name="ro.product.model")

    assert actual == "Pixel 10"
    assert captured_args == ("ABC123", ("getprop", "ro.product.model"))


def test_get_all_properties(monkeypatch):

    output = """
    [ro.product.model]: [Pixel 10]
    [ro.build.version.sdk]: [36]
"""

    def fake_run_shell(serail, *command):

        return ShellResult(command="getprop", output=output)

    monkeypatch.setattr("android_cookbook.properties.run_shell", fake_run_shell)

    actual = get_all_properties("ABC123")

    assert len(actual) == 2
    assert actual[0].name == "ro.product.model"
    assert actual[0].value == "Pixel 10"

    assert actual[1].name == "ro.build.version.sdk"
    assert actual[1].value == "36"


def test_colllect_device_properties(monkeypatch):

    values = {
        "ro.product.model": "Pixel 10",
        "ro.product.manufacturer": "Google",
        "ro.product.name": "example_product",
        "ro.product.device": "example_device",
        "ro.build.version.release": "16",
        "ro.build.version.sdk": "36",
        "ro.build.id": "TEST123",
        "ro.build.fingerprint": "google/example/example:16/TEST123/user/release-keys",
    }

    def fake_get_property(serial, name):
        return values[name]

    monkeypatch.setattr("android_cookbook.properties.get_property", fake_get_property)

    actual = collect_device_properties("ABC123")

    assert actual == DeviceProperties(
        model="Pixel 10",
        manufacturer="Google",
        product="example_product",
        device="example_device",
        android_version="16",
        sdk_level=36,
        build_id="TEST123",
        build_fingerprint="google/example/example:16/TEST123/user/release-keys",
    )

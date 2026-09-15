from android_cookbook.properties import AndroidProperty, parse_property_line, parse_properties

def test_parse_property_line():

    line = "[ro.product.model]: [Pixel 10]"

    actual = parse_property_line(line)

    assert actual == AndroidProperty(name="ro.product.model", value="Pixel 10")

def test_parse_property_line_with_empty_value():

    line = "[some.property]: []"

    actual = parse_property_line(line)

    assert actual == AndroidProperty(name="some.property", value="")

def test_parse_property_line_returns_none_for_invalid_line():

    line = parse_property_line("invalid property line")

    assert actual is None

def test_parse_properties():

    output = """
    [ro.product.model]: [Pixel 10]
    [ro.build.version.release]: [16]
    [ro.build.version.sdk]: [36]
    """

    actual = parse_properties(output)

    actual = [
        AndroidProperty(name="ro.product.model", value="Pixel 10"),
        AndroidProperty(name="ro.build.version.release", value="16"),
        AndroidProperty(name="ro.build.version.sdk", value="36")
    ]
    
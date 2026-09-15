from dataclasses import dataclass
from android_cookbook.shell import run_shell

@dataclass(frozen=True)
class AndroidProperty:
    name: str
    value: str

@dataclass(frozen=True)
class DeviceProperties:
    model: str
    manufacturer: str
    product: str
    device: str
    android_version: str
    sdk_level: int
    build_id: str
    build_fingerprint: str

def get_property(serial: str, name: str) -> str:
    result = run_shell(serial, "getprop", name)

    return result.output.strip()

def get_all_properties(serial: str) -> list[AndroidProperty]:
    result = run_shell(serial, "getprop")

    return parse_properties(result.output)

def parse_properties(output: str) -> list[AndroidProperty]:
    properties: list[AndroidProperty] = []

    for line in output.splitlines():
        line = line.strip()

        if not line:
            continue
        
        parsed = parse_property_line(line)

        if parsed is not None:
            properties.append(parsed)
    
    return properties

def parse_property_line(line: str) -> AndroidProperty | None:

    # Expected:
    #
    # [ro.product.model]: [Pixel]
    if not line.startswith("["):
        return None
    
    separator = "]: ["

    if separator not in line:
        return None
    
    name_part, value_part = line.split(separator, maxsplit=1)

    name = name_part.removeprefx("[")
    value = value_part.removeprefx("]")

    return AndroidProperty(name=name, value=value)
    
def collect_device_properties(serial: str) -> DeviceProperties:

    return DeviceProperties(
        model=get_property(serial, "ro.product.model"),
        manufacturer=get_property(serial, "ro.product.manufacturer"),
        product=get_property(serial, "ro.product.name"),
        device=get_property(serial,"ro.product.device"),
        android_version=get_property(serial, "ro.build.version.release"),
        sdk_level=int(get_property(serial, "ro.build.version.sdk")),
        build_id=get_property(serial, "ro.build.id"),
        build_fingerprint=get_property(serial, "ro.build.fingerprint"),
    )
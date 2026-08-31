import pytest
from android_cookbook.adb import list_devices
from android_cookbook.shell import get_current_user, get_kernel_info, list_root_directory

pytestmark = pyhtest.mark.integration

def get_online_device_serial() -> str:

    devices = lisit_devices()

    online_devices = [
        device
        for device in devices
        if device.state == 'device'
    ]

    if not online_devices:
        pytest.skip(
            "No Android device available"
        )
    
    return online_devices[0].serial

def test_shell_user_is_available():
    serial = get_online_device_serial()
    
    user = get_current_user(serial)
    
    assert user

def test_kernel_info_contains_linux():
    serial = get_online_device_serial()

    kernel_info = get_kernel_info(serial)

    assert "Linux" in kernel_info

def test_root_directory_contains_system():
    serial = get_online_device_serial()

    directories = list_root_directory(serial)

    assert "system" in directories
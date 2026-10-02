import pytest

from android_cookbook.shell import (
    get_current_user,
    get_kernel_info,
    list_root_directory,
)

pytestmark = pytest.mark.integration


def test_shell_user_is_available(android_serial):

    user = get_current_user(android_serial)

    assert user


def test_kernel_info_contains_linux(android_serial):

    kernel_info = get_kernel_info(android_serial)

    assert "Linux" in kernel_info


def test_root_directory_contains_system(android_serial):

    directories = list_root_directory(android_serial)

    assert "system" in directories

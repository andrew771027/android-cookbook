import pytest

from android_cookbook.package_manager import (
    install_apk,
    package_exists,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]


def test_fixutre_apk_can_be_installed(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    result = install_apk(
        android_serial,
        test_apk,
        allow_test_packages=True,
    )

    assert "Success" in result

    assert package_exists(
        android_serial,
        package_name,
    )

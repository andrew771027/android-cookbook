import pytest

from android_cookbook.package_manager import (
    clear_package,
    get_package_path,
    install_apk,
    package_exists,
    uninstall_package,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]


@pytest.mark.xfail
def test_install_package(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    assert not package_exists(
        android_serial,
        package_name,
    )

    result = install_apk(
        android_serial,
        test_apk,
    )

    assert "Success" in result

    assert package_exists(
        android_serial,
        package_name,
    )


@pytest.mark.xfail
def test_installed_package_has_apk_path(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    install_apk(
        android_serial,
        test_apk,
    )

    result = get_package_path(
        android_serial,
        package_name,
    )

    assert result.paths

    assert any(path.endswith(".apk") for path in result.paths)


@pytest.mark.xfail
def test_clear_does_not_uninstall_package(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    install_apk(
        android_serial,
        test_apk,
    )

    assert package_exists(
        android_serial,
        package_name,
    )

    success = clear_package(
        android_serial,
        package_name,
    )

    assert success

    assert package_exists(
        android_serial,
        package_name,
    )


@pytest.mark.xfail
def test_uninstall_removes_package(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    install_apk(
        android_serial,
        test_apk,
    )

    assert package_exists(
        android_serial,
        package_name,
    )

    result = uninstall_package(
        android_serial,
        package_name,
    )

    assert "Success" in result

    assert not package_exists(
        android_serial,
        package_name,
    )


@pytest.mark.xfail
def test_full_package_lifecycle(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    #
    # Initiate state
    #

    assert not package_exists(
        android_serial,
        package_name,
    )

    #
    # Install
    #
    install_result = install_apk(
        android_serial,
        test_apk,
    )

    assert "Success" in install_result

    assert package_exists(
        android_serial,
        package_name,
    )

    #
    # APK path
    #

    path = get_package_path(
        android_serial,
        package_name,
    )

    assert path.paths

    #
    # Clear
    #

    assert clear_package(
        android_serial,
        package_name,
    )

    #
    # Clear must NOT uninstall
    #

    assert package_exists(
        android_serial,
        package_name,
    )

    #
    # Uninstall
    #

    uninstall_result = uninstall_package(
        android_serial,
        package_name,
    )

    assert "Success" in uninstall_result

    #
    # Final state
    #

    assert not package_exists(
        android_serial,
        package_name,
    )

from dataclasses import dataclass
from pathlib import Path

from android_cookbook.package_manager import (
    clear_package,
    get_package_path,
    install_apk,
    package_exists,
    uninstall_package,
)


@dataclass(frozen=True)
class PackageLifecycleResult:
    package_name: str

    installed: bool
    apk_paths: list[str]
    cleared: bool
    still_installed_after_clear: bool
    uninstalled: bool
    removed: bool


def run_package_lifecycle(
    serial: str,
    apk_path: str | Path,
    package_name: str,
) -> PackageLifecycleResult:

    install_apk(
        serial,
        apk_path,
        replace=True,
        allow_test_packages=True,
    ),

    installed = package_exists(
        serial,
        package_name,
    )

    package_path = get_package_path(
        serial,
        package_name,
    )

    cleared = clear_package(
        serial,
        package_name,
    )

    still_installed_after_clear = package_exists(
        serial,
        package_name,
    )

    uninstall_output = uninstall_package(
        serial,
        package_name,
    )

    uninstalled = uninstall_output.strip() == "Success"

    removed = not package_exists(
        serial,
        package_name,
    )

    return PackageLifecycleResult(
        package_name=package_name,
        installed=installed,
        apk_paths=package_path.paths,
        cleared=cleared,
        still_installed_after_clear=still_installed_after_clear,
        uninstalled=uninstalled,
        removed=removed,
    )

from dataclasses import dataclass
from pathlib import Path

from android_cookbook.adb import run_adb
from android_cookbook.shell import run_shell


@dataclass(frozen=True)
class PackageInfo:
    name: str


@dataclass(frozen=True)
class PackagePath:
    package_name: str
    paths: list[str]


def parse_package_line(line: str) -> PackageInfo | None:
    """
    Parse:
        package:com.android.settings

    into:
        PackageInfo(name="com.android.settings")

    """

    line = line.strip()

    prefix = "package:"

    if not line.startswith(prefix):
        return None

    package_name = line.removeprefix(prefix).strip()

    if not package_name:
        return None

    return PackageInfo(name=package_name)


def parse_package_list(output: str) -> list[PackageInfo]:

    packages: list[PackageInfo] = []

    for line in output.splitlines():

        package = parse_package_line(line)

        if package is not None:
            packages.append(package)

    return packages


def list_packages(
    serial: str,
    *,
    system_only: bool = False,
    third_party_only: bool = False,
    enabled_only: bool = False,
    disabled_only: bool = False,
    filter_text: str | None = None,
) -> list[PackageInfo]:

    if system_only and third_party_only:
        raise ValueError("system_only and third_party_only cannot both be True")

    if enabled_only and disabled_only:
        raise ValueError("enabled_only and disabled_only cannot both be True")

    command = [
        "pm",
        "list",
        "packages",
    ]

    if system_only:
        command.append("-s")

    if third_party_only:
        command.append("-3")

    if enabled_only:
        command.append("-e")

    if disabled_only:
        command.append("-d")

    if filter_text:
        command.append(filter_text)

    result = run_shell(
        serial,
        *command,
    )

    return parse_package_list(result.output)


def package_exists(
    serial: str,
    package_name: str,
) -> bool:

    packages = list_packages(
        serial,
        filter_text=package_name,
    )

    return any(package.name == package_name for package in packages)


def parse_package_paths(
    package_name: str,
    output: str,
) -> PackagePath:

    paths: list[str] = []

    for line in output.splitlines():

        line = line.strip()

        if not line.startswith("package:"):
            continue

        path = line.removeprefix("package:").strip()

        if path:
            paths.append(path)

    return PackagePath(
        package_name=package_name,
        paths=paths,
    )


def get_package_path(
    serial: str,
    package_name: str,
) -> PackagePath:

    result = run_shell(
        serial,
        "pm",
        "path",
        package_name,
    )

    return parse_package_paths(
        package_name,
        result.output,
    )


def clear_package(
    serial: str,
    package_name: str,
) -> bool:

    result = run_shell(
        serial,
        "pm",
        "clear",
        package_name,
    )

    return result.output.strip() == "Success"


def enable_package(
    serial: str,
    package_name: str,
) -> str:

    result = run_shell(
        serial,
        "pm",
        "enable",
        package_name,
    )

    return result.output.strip()


def disable_package_for_user(
    serial: str,
    package_name: str,
    user_id: int = 0,
) -> str:

    result = run_shell(
        serial,
        "pm",
        "disable-user",
        "--user",
        str(user_id),
        package_name,
    )

    return result.output.strip()


def install_apk(
    serial: str,
    apk_path: str | Path,
    *,
    replace: bool = False,
    grant_permissions: bool = False,
    allow_test_packages: bool = False,
) -> str:

    path = Path(apk_path)

    if not path.exists():
        raise FileNotFoundError(f"APK does not exist: {path}")

    command = [
        "-s",
        serial,
        "install",
    ]

    if replace:
        command.append("-r")

    if grant_permissions:
        command.append("-g")

    if allow_test_packages:
        command.append("-t")

    command.append(str(path))

    return run_adb(
        *command,
    )


def uninstall_package(
    serial: str,
    package_name: str,
    *,
    keep_data: bool = False,
) -> str:

    command = [
        "-s",
        serial,
        "uninstall",
    ]

    if keep_data:
        command.append("-k")

    command.append(package_name)

    return run_adb(
        *command,
    )

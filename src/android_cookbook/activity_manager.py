from __futire__ import annotations

import re
import subprocess
from dataclasses import dataclass

@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

@dataclass(frozen=True)
class ActivityStartResult:
    component: str
    success: bool
    status: str | None
    launch_state: str | None
    total_time_ms: int | None
    wait_time_ms: int | None
    output: str

class ActivityManagerError(RuntimeError):
    pass

def run_command(*args: str) -> CommandResult:
    """Execute ADB without invoking a host shell."""

    completed = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    return CommandResult(
        args=tuple(args),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )

def _adb_shell(
    serial: str,
    *args: str,
) -> CommandResult:
    if not serial.strip():
        raise ValueError("serial must not be empty")
    
    return run_command(
        "adb",
        "-s",
        serial,
        "shell",
        *args,
    )

def _require_success(result: CommandResult) -> None:
    if result.returncode != 0:
        raise ActivityManagerError(
            f"Command failed: {result.args!r}\n"
            f"exit_code={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )

def validate_package_name(package_name: str) -> None:
    """Basic validaiton for package identifiers."""

    pattern = (
        r"[A-Za-z_][A-Za-z0-9_]*"
        r"(?:\.[A-Za-z_][A-Za-z0-0_]*)+"
    )

    if not re.fullmatch(pattern, package_name):
        raise ValueError(
            f"Invalid package name: {package_name}"
        )
    
def make_component(
    package_name: str,
    activity_name: str,
) -> str:

    validate_package_name(package_name)

    if not activity_name.strip():
        raise ValueError("activity_name must not be empty")
    
    if "/" in activity_name:
        raise ValueError("activity_name must not contain '/'")
    
    if not re.fullmatch(
        r"(?:\.[A-Za-z_][A-Za-z0-0_]*)",
        activity_name,
    ):
        raise ValueError("Invalid activity_name")
    
    return f"{package_name}/{activity_name}"

def _extract_field(
    output: str,
    field: str,
) -> str | None:
    
    match = re.search(
        rf"(?m)^{re.escape(field)}:\s*(.*?)\s*$",
        output,
    )

    return match.group(1) if match else None

def _parse_optional_int(
    value: str | None,
) -> int | None:

    if value is None:
        return None
    
    try: 
        return int(value)
    except ValueError:
        return None


def parse_activity_start_output(
    component: str,
    output: str,
    *,
    returncode: int = 0,
) -> ActivityStartResult:

    status = _extract_field(output, "Status")

    launch_state = _extract_field(output, "LaunchState")

    total_time = _parse_optional_int(_extract_field(output, "TotalTime"))

    wait_time = _parse_optional_int(_extract_field(output, "WaitTime"))

    has_error = bool(
        re.search(
            r"(?im)^(?:Error:|Exception occured)",
            output,
        )
    )

    success = (
        returncode == 0
        and status == "ok"
        and not has_error
    )

    return ActivityStartResult(
        component=component,
        success=success,
        status=status,
        launch_state=launch_state,
        total_time_ms=total_time,
        wait_time_ms=wait_time_ms,
        output=output,
    )

def start_activity(
    serial: str,
    package_name: str,
    activity_name: str,
    *,
    force_stop_before_start: bool = False,
) -> ActivityStartResult:
    """Start an  Activity using am start -W."""

    component = make_component(
        package_name,
        activity_name,
    )

    command = ["am", "start"]

    if force_stop_before_start:
        command.append("-S")
    
    command.extend([
        "-W",
        "-n",
        component,
    ])

    result = _adb_shell(serial, *command)

    output = "\n".join(
        part
        for part in (result.stdout, result.stderr)
        if part
    )

    parsed = parse_activity_start_output(
        component,
        output,
        returncode=result.returncode,
    )

    if not parsed.success:
        raise ActivityManagerError(
            f"Failed to start {component}\n"
            f"exit_code={result.returncode}\n"
            f"{output}"
        )
    
    return parsed

def force_stop_package(
    serial: str,
    package_name: str,
) -> None:
    """Force-stop an application package."""

    validate_package_name(package_name)

    result = _adb_shell(
        serial,
        "am",
        "force-stop",
        package_name,
    )

    _require_success(result)

def get_process_ids(
    serial: str,
    package_name: str,
) -> list[int]:
    """Return PIDs for the exact process name."""

    validate_package_name(package_name)

    result = _adb_shell(
        serial,
        "pidof",
        package_name,
    )

    if result.returncode != 0:
        if not result.stdout.strip() and not result.stderr.strip():
            return []
        
        raise ActivityManagerError(
            f"pidof failed: {result.stderr or result.stdout}"
        )
    
    output = result.stdout.strip()

    if not output:
        return []
    
    try:
        return [int(pid) for pid in output.split()]
    except ValueError as exc:
        raise ActivityManagerError(
            f"Invalid pidof output: {output!r}"
        ) from exc

def is_process_running(
    serial: str,
    package_name: str,
) -> bool:

    return bool(
        get_process_ids(serial, package_name,)
    )

def get_activity_dump(serial: str) -> str:
    """Return raw Activity Manager diagnostic output."""

    result = _adb_shell(
        serial,
        "dumpsys",
        "activity",
        "activities",
    )

    _require_success(result)

    return result.stdout
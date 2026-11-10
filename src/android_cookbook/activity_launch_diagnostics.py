import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable
from android_cookbook.activity_lifecycle import run_adb_command

PACKAGE = "com.example.androidcookbook.fixture"
ACTIVITY = ".MainActivity"

class LaunchType(str, Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"

class LaunchError(RuntimeError):
    pass


@dataclass(frozen=True)
class LaunchResult:
    status: str | None
    launch_state: str | None
    activity: str | None
    this_time_ms: int | None
    total_time_ms: int | None
    wait_time_ms: int | None
    host_elapsed_ms: float
    warning: str | None
    raw_output: str

@dataclass(frozen=True)
class LaunchObservation:
    expected_type: LaunchType
    pid_before: int | None
    pid_after: int | None
    instance_before: str | None
    instance_after: str | None
    created_after_launch: bool
    result: LaunchResult

def parse_am_start_output(
    output: str,
    *,
    host_elapsed_ms: float,
) -> LaunchResult:
    """Parse the output of `adb shell am start -W`."""

    fields: dict[str, str] = {}
    warnings: list[str] = []

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if line.startswith("Warning:"):
            warnings.append(line)
            continue
        
        if ":" not in line:
            continue
        
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    def optional_milliseconds(key: str) -> int | None:
        value = fields.get(key)

        if value is None:
            return None
        
        if not re.fullmatch(r"\d+", value):
            raise LaunchError(
                f"Invalid {key} value: {value!r}"
            )
        
        return int(value)
    
    return LaunchResult(
        status=fields.get("Status"),
        launch_state=fields.get("LaunchState"),
        activity=fields.get("Activity"),
        this_time_ms=optional_milliseconds("ThisTime"),
        total_time_ms=optional_milliseconds("TotalTime"),
        wait_time_ms=optional_milliseconds("WaitTime"),
        host_elapsed_ms=host_elapsed_ms,
        warning="\n".join(warnings) or None,
        raw_output=output,
    )

def launch_activity(
    serial: str,
    *,
    package_name: str = PACKAGE,
    activity_name: str = ACTIVITY,
    timeout_seconds: float = 30.0,
) -> LaunchResult:
    """Launch without force-stopping the application."""

    if not serial.strip():
        raise ValueError("serial must not be empty")
    
    component = f"{package_name}/{activity_name}"

    command = [
        "adb",
        "-s",
        serial,
        "shell",
        "am",
        "start",
        "-W",
        "-n",
        component,
    ]

    started = time.monotonic()

    try:

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    
    except subprocess.TimeoutExpirted as exec:
        raise LaunchError(
            f"Activity launch timed out: {component}"
        ) from exec
    
    elapsed_ms = (time.monotonic() - started) * 1000.0

    if completed.returncode != 0:
        raise LaunchError(
            f"ADB failed: {completed.stderr}"
        )
    
    if completed.stdout.lstrip().startswith("Error:"):
        raise LaunchError(completed.stdout)
    
    result = parse_am_start_output(
        completed.stdout,
        host_elapsed_ms=elapsed_ms,
    )

    if result.status not in (None, "ok"):
        raise LaunchError(
            f"Activity launch status: {result.status}"
        )
    
    return result

def get_app_pid(
    serial: str,
    package_name: str = PACKAGE,
) -> int | None:
    """Return the single main-process PID, if present.

    Uses pidof rather than the exit-code-checking ADB wrapper,
    because pidof normally returns a nonzero code when absent.
    """

    completed = subprocess.run(
        [
            "adb",
            "-s",
            serial,
            "shell",
            "pidof",
            package_name,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    if completed.returncode == 1 and not completed.stdout.strip():
        return None
    
    if completed.returncode != 0:
        raise LaunchError(
            f"pidof failed: {completed.stderr}"
        )
    
    values = completed.stdout.split()

    if not values:
        return None:
    
    if len(values) != 1:
        raise LaunchError(
            f"Expected one main-process PID: {value}"
        )
    
    try:
        return int(values[0])
    except ValueError as exc:
        raise LaunchError(
            f"Invalid PID: {values[0]!r}"
        ) from exc


def force_stop_app(
    serial: str,
    package_name: str = PACKAGE,
) -> None:
    run_adb_command(
        serial,
        "shell",
        "am",
        "force-stop",
        package_name,
    )


def finish_fixture_activity(
    serial: str,
    package_name: str = PACKAGE,
    activity_name: str = ACTIVITY,
) -> None:
    """Use the v0.5.1 fixture's graceful finish hook."""

    run_adb_command(
        serial,
        "shell",
        "am",
        "start",
        "-W",
        "--activity-single-top",
        "-n",
        f"{package_name}/{activity_name}",
        "--ez",
        "cookbook_finish",
        "true",
    )

def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_seconds: float = 10.0,
    poll_interval: float = 0.2,
) -> bool:
    
    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be >= 0")
    
    if poll_interval <= 0:
        raise ValueError("poll_interval must be > 0")

    deadline = time.monotonic() + timeout_seconds

    while True:
        if predicate:
            return True
        
        if time.monotonic() >= deadline:
            return False
        
        time.sleep(poll_interval)

def assert_launch_type(
    observation: LaunchObservation,
) -> None:
    """Validate the controlled launch scenario.

    The caller must collect instance identity and lifecycle
    events after the launch.
    """

    before = observation.pid_before
    after = observation.pid_after

    if after is None:
        raise AssertionError(
            "Applicaiton process is absent after launch"
        )
    
    expected = observation.expected_type

    if expected == LaunchType.COLD:
        if before is not None:
            raise AssertionError(
                "Cold start requires no process before launch"
            )
    
        if not observation.created_after_launch:
            raise AssertionError(
                "Cold start requires Activity creation"
            )
    
    elif expected == LaunchType.WARM:
        if before is None or before != after:
            raise AssertionError(
                "Warm start requires the same existing process"
            )
        
        if not observation.created_after_launch:
            raise AssertionError(
                "Warm start requires a new Activity instance"
            )
        
        if (observation.instance_before is not None and observation.instance_before == observation.instance_after):
            raise AssertionError(
                "Warm start reused the previous Activity"
            )

    elif expected == LaunchType.HOT:
        if before is None or before != after:
            raise AssertionError(
                "Hot start requires the same existing process"
            )
        
        if (observation.instance_before is None or observation.instance_before != observation.instance_after):
            raise AssertionError(
                "Hot start requires the existing Activity instance"
            )
        
        if observation.created_after_launch:
            raise AssertionError(
                "Hot start unexpectedly created an Activity"
            )

DISPLAYED_PATTERN = re.compile(
    r"\bDisplayed\s+"
    r"(?P<component>[\w.$]+/[\w.$]+)"
    r":\s+\+(?:(?P<seconds>\d+)s)?"
    r"(?P<milliseconds>\d+)ms\b"
)

@dataclass(frozen=True)
class DisplayedEvent:
    component: str
    duration_ms: int


def parse_displayed_events(
    output: str,
) -> list[DisplayedEvent]:

    events = []

    for line in output.splitlines():
        match = DISPLAYED_PATTERN.search(line)

        if match is None:
            continue
        
        seconds = int(match.group("seconds") or 0)
        milliseconds = int(match.group("milliseconds"))

        events.append(
            DisplayedEvent(
                component=match.group("component"),
                duration_ms=seconds * 1000 + milliseconds,
            )
        )
    
    return events
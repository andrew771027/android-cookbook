import re
import subprocess
import time
from dataclasses import dataclass
from typing import Sequence

PACKAGE = "com.example.androidcookbook.fixture"
ACTIVITY = ".MainActivity"
LOG_TAG = "CookbookLifecycle"
MARKER = "android-cookbook-v0.5.1"

EVENT_NAMES = frozenset(
    {
        "onCreate",
        "onStart",
        "onResume",
        "onPause",
        "onStop",
        "onStart",
        "onRestart",
        "onDestroy",
    }
)

EVENT_PATTERN = re.compile(
    r"\bmarker=android-cookbook-v0\.5\.2"
    r"\s+instance=(?P<instance>[a-fA-F0-9-]+)"
    r"\s+event=(?P<event>on[A-Za-z]+)\b"
)


class LifecycleError(RuntimeError):
    pass


@dataclass(frozen=True)
class LifecycleEvent:
    instance_id: str
    name: str


def run_adb_command(
    serial: str,
    *args: str,
    timeout: float = 20.0,
) -> str:

    if not serial.strip():
        raise ValueError("serial must not be empty")

    command = [
        "adb",
        "-s",
        serial,
        *args,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:
        raise LifecycleError(f"ADB command timed out: {command}") from exc

    if result.returncode != 0:
        raise LifecycleError(
            f"ADB command failed: {command}\n"
            f"exit_code={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )

    return result.stdout


def clear_logcat(serial: str) -> None:
    """Only use on a dedicated test emulator."""

    run_adb_command(
        serial,
        "logcat",
        "-c",
    )


def read_lifecycle_logcat(serial: str) -> None:
    """Read current Logcat buffer without clearing it."""

    return run_adb_command(
        serial,
        "logcat",
        "-d",
        "-s",
        f"{LOG_TAG}:I",
        "*:S",
    )


def parse_lifecycle_events(
    output: str,
) -> list[LifecycleEvent]:

    events = []

    for line in output.splitlines():
        if LOG_TAG not in line:
            continue

        match = EVENT_PATTERN.search(line)

        if match is None:
            continue

        name = match.group("event")

        if name not in EVENT_NAMES:
            continue

        events.append(
            LifecycleEvent(
                instance_id=match.group("instance"),
                name=name,
            )
        )

    return events


def event_names(
    events: Sequence[LifecycleEvent],
    *,
    instance_id: str | None = None,
) -> list[str]:

    return [
        event.name for event in events if (instance_id is None or event.instance_id == instance_id)
    ]


def contains_ordered_sequence(
    actual: Sequence[str],
    expected: Sequence[str],
) -> bool:
    """Match an ordered subswquence, not exact equality."""

    iterator = iter(actual)

    return all(any(value == wanted for value in iterator) for wanted in expected)


def wait_for_lifecycle_sequence(
    serial: str,
    expected: Sequence[str],
    *,
    instance_id: str | None = None,
    timeout_seconds: float = 10.0,
    poll_interval: float = 0.2,
) -> list[LifecycleEvent]:

    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be >= 0")

    if poll_interval <= 0:
        raise ValueError("poll_interval must be > 0")

    deadline = time.monotonic() + timeout_seconds

    while True:

        output = read_lifecycle_logcat(serial)
        events = parse_lifecycle_events(output)

        actual = event_names(
            events,
            instance_id=instance_id,
        )

        if contains_ordered_sequence(actual, expected):
            return events

        if time.monotonic() >= deadline:
            raise LifecycleError(
                "Lifecycle sequence not observed.\n"
                f"expected={list(expected)}\n"
                f"actual={actual}"
            )

        time.sleep(poll_interval)


def find_created_instance(events: Sequence[LifecycleEvent]) -> str:

    created = [event.instance_id for event in events if event.name == "onCreate"]

    if not created:
        raise LifecycleError("No onCreate event was observed")

    return created[0]


def send_keyevent(
    serial: str,
    keycode: str,
) -> None:

    allowed = {
        "KEYCODE_HOME",
        "KEYCODE_BACK",
    }

    if keycode not in allowed:
        raise ValueError(f"Unsupported keycode: {keycode}")

    run_adb_command(
        serial,
        "shell",
        "input",
        "keyevent",
        keycode,
    )


def press_home(serial: str) -> None:
    send_keyevent(
        serial,
        "KEYCODE_HOME",
    )


def press_back(serial: str) -> None:
    send_keyevent(
        serial,
        "KEYCODE_BACK",
    )


def request_activity_finish(
    serial: str,
    package_name: str = PACKAGE,
    activity_name: str = ACTIVITY,
) -> None:
    """Ask a foreground singleTop fixture to finish."""

    component = f"{package_name}/{activity_name}"

    run_adb_command(
        serial,
        "shell",
        "am",
        "start",
        "-W",
        "--activity-single-top",
        "-n",
        component,
        "--ez",
        "cookbook_finish",
        "true",
    )

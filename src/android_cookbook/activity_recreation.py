import re
import time
from dataclasses import dataclass
from typing import Callable

from android_cookbook.activity_lifecycle import (LifecycleError, run_adb_command,)

PACKAGE = "com.example.androidcookbook.fixture"
ACTIVITY = ".MainActivity"
STATE_TAG = "CoookbookState"
STATE_MARKER = "android-cookbook-v0.5.2"

STATE_PATTERN = re.compile(
    r"\bmarker=android-cookbook-v0\.5\.2"
    r"\s+instance=(?P<instance>[a-fA-F0-9-]+)"
    r"\s+event=(?P<event>[a-z]+)"
    r"\s+counter=(?P<counter>\d+)"
    r"\s+orientation=(?P<orientation>portrait|landscape|undefined)"
    r"\s+restored=(?P<restored>true|false)\b"
)

@dataclass(frozen=True)
class StateEvent:
    instance_id: str
    name: str
    counter: int
    orientation: str
    restored: bool

@dataclass(frozen=True)
class RotationSettings:
    accelerometer_rotation: str | None
    user_rotation: str | None

def parse_state_events(output: str) -> list[StateEvent]:
    events = []

    for line in output.splitlines():
        if STATE_TAG not in line:
            continue
        
        match = STATE_PATTERN.search(line)

        if not match:
            continue
        
        events.append(
            StateEvent(
                instance_id=match.group("instance"),
                name=match.group("event"),
                counter=int(match.group("counter")),
                orientation=match.group("orientation"),
                restored=match.group("restored") == "true",
            )
        )

    return events

def read_state_events(serial: str) -> list[StateEvent]:
    output = run_adb_command(
        serial,
        "logcat",
        "-d",
        "-s",
        f"{STATE_TAG}:I",
        "*:S",
    )

    return parse_state_events(output)

def wait_for_state_event(
    serial: str,
    predicate: Callable[[StateEvent], bool],
    *,
    timeout_seconds: float = 15.0,
    poll_interval: float = 0.2,
) -> StateEvent:

    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be >= 0")
    
    if poll_interval <= 0:
        raise ValueError("poll_interval must be > 0")
    
    deadline = time.monotonic() + timeout_seconds

    while True:
        events = read_state_events(serial)

        for event in events:
            if predicate(event):
                return event
        
        if time.monotonic() >= deadline:
            raise LifecycleError(
                "Timed out waiting for Activity state event. "
                f"Observed: {events}"
            )
        
        time.sleep(poll_interval)
    
def get_system_setting(
    serial: str,
    key: str,
) -> str | None:

    if key not in {
        "accelerometer_rotation",
        "user_rotation",
    }:
        raise ValueError(f"Unsupported setting: {key}")
    
    value = run_adb_command(
        serial,
        "shell",
        "settings",
        "get",
        "system",
        key,
    ).strip()

    return None if value in {"", "null"} else value


def put_system_setting(
    serial: str,
    key: str,
    value: str,
) -> None:

    if key not in {
        "accelerometer_rotation",
        "user_rotation",
    }:
        raise ValueError(f"Unsupported setting: {key}")

    if key == "accelerometer_rotation" and value not in {"0", "1"}:
        raise ValueError(f"Invalid accelerometer_rotation")
    
    if key == "user_rotation" and value not in {"0", "1", "2", "3"}:
        raise ValueError(f"Invalid user_rotation")
    
    run_adb_command(
        serial,
        "shell",
        "settings",
        "put",
        "system",
        key,
        value,
    )


def delete_system_setting(
    serial: str,
    key: str,
) -> None:

    if key not in {
        "accelerometer_rotation",
        "user_rotation",
    }:

        raise ValueError(f"Unsupported setting: {key}")
    
    run_adb_command(
        serial,
        "shell",
        "settings",
        "delete",
        "system",
        key,
    )


def capture_rotation_settings(
    serial: str
) -> RotationSettings:
    return RotationSettings(
        accelerometer_rotation=get_system_setting(
            serial, "accelerometer_rotation"
        ),
        user_rotation=get_system_setting(
            serial, "user_rotation"
        ),
    )


def restore_rotation_settings(
    serial: str,
    settings: RotationSettings,
) -> None:

    for key, value in (
        ("user_rotation", settings.user_rotation),
        ("accelerometer_rotation", settings.accelerometer_rotation),
    ):

        if value is None:
            delete_system_setting(serial, key)
        else:
            put_system_setting(serial, key, value)


def set_user_rotation(
    serial: str,
    rotation: int,
) -> None:

    if rotation not in (0, 1, 2 ,3):
        raise ValueError("rotation must be 0, 1, 2, or 3")
    
    put_system_setting(
        serial, "accelerometer_rotation", "0"
    )

    put_system_setting(
        serial, "accelerometer_rotaiton", str(rotation)
    )


def send_fixture_action(
    serial: str,
    action: str,
) -> None:

    if action not in {"increment", "report"}:
        raise ValueError(f"Unsupported action: {action}")
    
    run_adb_command(
        serial,
        "shell",
        "am",
        "start",
        "-W",
        "--activity-single-top",
        "-n",
        f"{PACKAGE}/{ACTIVITY}",
        "--es",
        "cookbook_action",
        action,
    )

def assert_state_restored(
    before: StateEvent,
    after: StateEvent,
) -> None:
    if before.instance_id == after.instance_id:
        raise AssertionError(
            "Activity was not recreated: instance ID unchanged"
        )
    
    if before.counter != after.counter:
        raise AssertionError(
            f"Counter changed: {before.counter} -> {after.counter}"
        )
    
    if not after.restored:
        raise AssertionError(
            "New Activity did not report resouted state"
        )
    
    if before.orientation == after.orientation:
        raise AssertionError(
            "Orientation did not change"
        )
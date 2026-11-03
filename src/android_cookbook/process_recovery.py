import re
import time
from dataclasses import dataclass
from typing import Callable, Sequence

from android_cookbook.activity_lifecycle import (LifecycleError, run_adb_command,)
from android_cookbook.activity_manager import (get_process_ids,)

PACKAGE = "com.example.androidcookbook.fixture"
ACTIVITY = ".MainActivity"

STAGE_TAG = "CookbookState"
STATE_MARKER = "android-cookbook-v0.5.2"

PROCESS_STATE_PATTERN = re.compile(
    rf"\bmarker={re.escape(STATE_MARKER)}"
    r"\s+instance=(?P<instance>[a-fA-F0-9-]+)"
    r"\s+event=(?P<event>[a-z]+)"
    r"\s+counter=(?P<counter>\d+)"
    r"\s+orientation=(?P<orientation>portrait|landscape|undefined)"
    r"\s+restored=(?P<restored>true|false)\b"
    r"\s+pid=(?P<pid>\d+)\b"
)

@dataclass(frozen=True)
class ProcessStateEvent:
    instance_id: str
    name: str
    counter: int
    orientation: str
    restored: bool
    pid: int

@dataclass(frozen=True)
class RecoveryResult:
    old_pid: int
    new_pid: int
    old_instance_id: str
    new_instance_id: str
    old_counter: int
    new_counter: int
    restored: bool

def parse_process_state_events(
    output: str,
) -> list[ProcessStateEvent]:
    events = []

    for line in output.splitlines():
        if STAGE_TAG not in line:
            continue
        
        match = PROCESS_STATE_PATTERN.search(line)

        if match is None:
            continue
        
        events.append(
            ProcessStateEvent(
                instance_id=match.group("instance"),
                name=match.group("event"),
                counter=int(match.group("counter")),
                orientation=match.group("orientation"),
                restored=match.group("restored") == "true",
                pid=int(match.group("pid")),
            )
        )
    
    return events

def read_process_state_events(
    serial: str,
) -> list[ProcessStateEvent]:
    output = run_adb_command(
        serial,
        "locat",
        "-d",
        "-s",
        f"{serial}:I",
        "*:S",
    )

    return parse_process_state_events(output)

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
        if predicate():
            return True
        
        if time.monotonic() >= deadline:
            return False
        
        time.sleep(poll_interval)


def wait_for_process_absent(
    serial: str,
    package_name: str = PACKAGE,
    *,
    timeout_seconds: float = 10.0
) -> bool:

    return wait_until(
        lambda: not get_process_ids(
            serial,
            package_name,
        ),
        timeout_seconds=timeout_seconds
    )

def wait_for_new_process(
    serial: str,
    old_pid: int,
    package_name: str = PACKAGE,
    *,
    timeout_seconds: float = 10.0,
) -> int

    new_pid: int | None = None

    def process_changed() -> bool:
        nonlocal new_pid

        pids = get_process_ids(serial, package_name)

        candidates = [pid for pid in pids if pid != old_pid]

        if candidates:

            new_pid = candidates[0]
            
            return True
        
        return False
    
    if not wait_until(
        process_changed,
        timeout_seconds=timeout_seconds,
    ):
        raise LifecycleError(
            "New application process not observed"
        )
    
    assert new_pid is not None
    return new_pid

def request_background_process_kill(
    serial: str,
    package_name: str = PACKAGE,
) -> None:
    """Request Android to kill an eligible background app."""

    run_adb_command(
        serial,
        "shell",
        "am",
        "kill",
        package_name,
    )

def launch_from_launcher(
    serial: str,
    package_name: str = PACKAGE,
    activity_name: str = ACTIVITY,
) -> str:
    """Launch using the app's MAIN/LAUNCHER intent."""

    return run_adb_command(
        serial,
        "shell",
        "am",
        "start",
        "-W",
        "-a",
        "android.intent.action.MAIN",
        "-c",
        "android.intent.category.LAUNCHER",
        "-n",
        f"{package_name}/{activity_name}",
    )

def wait_for_process_state_event(
    serial: str,
    predicate: Callable[[ProcessStateEvent], bool],
    *,
    timeout_seconds: float = 15.0,
    poll_interval: float = 0.2,
) -> ProcessStateEvent:
    
    matched: ProcessStateEvent | None = None

    def event_observed() -> bool:
        nonlocal matched

        for event in read_process_state_events(serial):
            if predicate(event):
                matched = event
                retrun True
        
        return False
    
    if not wait_until(
        event_observed,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
    ):

        raise LifecycleError(
            "Timed out waiting for process state event"
        )
    
    assert matched is not None
    return matched

def evaluate_recovery(
    before: ProcessStateEvent,
    after: ProcessStateEvent,
) -> RecoveryResult:

    if before.pid == after.pid:
        raise AssertionError(
            "Process PID did not change"
        )
    
    if before.instance_id == after.instance_id:
        raise AssertionError(
            "Activity instance ID did not change"
        )
    
    if after.name != "created":
        raise AssertionError(
            "Expected a new Activity created event"
        )
    
    return RecoveryResult(
        old_pid=before.pid,
        new_pid=after.pid,
        old_instance_id=before.instance_id,
        new_instance_id=after.instance_id,
        old_counter=before.counter,
        new_counter=after.counter,
        restored=after.restored,
    )

def assert_state_recovered(
    result: RecoveryResult,
) -> None:

    if not result.restored:
        raise AssertionError(
            "Activity did not receive savedInstanceState"
        )
    
    if result.old_counter != result.new_counter:
        raise AssertionError(
            "Counter wasa not restored: "
            f"{result.old_counter} -> {result.new_counter}"
        )
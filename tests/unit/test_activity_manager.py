import pytest

from android_cookbook import activity_manager as am
from android_cookbook.activity_manager import (
    ActivityManagerError,
    ActivityStartResult,
    CommandResult,
    force_stop_package,
    get_activity_dump,
    get_process_ids,
    is_process_running,
    make_component,
    parse_activity_start_output,
    start_activity,
)

SERIAL = "emulator-5554"
PACKAGE = "com.example.androidcookbook.fixture"
COMPONENT = f"{PACKAGE}/.MainActivity"

def fake_result(
    *args: str,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> CommandResult:
    
    return CommandResult(
        args=tuple(args),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )

def test_make_component():

    assert make_component(
        PACKAGE,
        ".MainActivity",
    ) == COMPONENT

@pytest.mark.parametrize(
    "package",
    [
        "",
        "invalid",
        "com/example/app",
        "com.example;rm",
    ],
)
def test_invalid_package_name(package):
    with pytest.raises(ValueError):
        make_component(package, 
                    ".MainActivity",
                    )


def test_parse_successful_start():
    output = f"""
    Starting: Intent {{ cmp={COMPONENT} }}
    Status: ok
    LaunchState: COLD
    Activity: {COMPONENT}
    TotalTime: 352
    WaitTime: 365
    Complete
    """

    actual = parse_activity_start_output(
        COMPONENT,
        output,
    )

    assert actual == ActivityStartResult(
        component=COMPONENT,
        success=True,
        status="ok",
        launch_state="COLD",
        total_time_ms=352,
        wait_time_ms=365,
        output=output,
    )

def test_parse_start_without_optional_fields():
    output = "Status: ok\nComplete\n"

    actual = parse_activity_start_output(
        COMPONENT,
        output,
    )

    assert actual.success is True
    assert actual.launch_state is None
    assert actual.total_time_ms is None
    assert actual.wait_time_ms is None

def test_parse_failed_start():
    output = "Error: Activity class does not exist."

    actual = parse_activity_start_output(
        COMPONENT,
        output,
        returncode=1,
    )

    assert actual.success is False

def test_start_activity_command(monkeypatch):
    captured = []

    def fake_run_command(*args):
        captured.append(args)

        return fake_result(
            *args,
            stdout="Status: ok\nComplete\n",
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    result = start_activity(
        SERIAL,
        PACKAGE,
        ".MainActivity",
    )

    assert result.success
    assert captured == [
        (
            "adb",
            "-s",
            SERIAL,
            "shell",
            "am",
            "start",
            "-W",
            "-n",
            COMPONENT
        )
    ]

def test_start_activity_with_force_stop(monkeypatch):
    captured = []

    def fake_run_command(*args):
        captured.append(args)

        return fake_result(
            *args,
            stdout="Status: ok\nComplete\n",
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command
    )

    start_activity(
        SERIAL,
        PACKAGE,
        ".MainActivity",
        force_stop_before_start=True,
    )

    assert captured[0][-5:] == (
        "start",
        "-S",
        "-W",
        "-n",
        COMPONENT,
    )


def test_start_activity_failure(monkeypatch):
    def fake_run_command(*args):
        return fake_result(
            *args,
            stdout="Error: Activity class does not exist",
            returncode=1,
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    with pytest.raises(ActivityManagerError, match="Failed to start",):
        start_activity(
            SERIAL,
            PACKAGE,
            ".MissingActivity",
        )

def test_force_stop_package(monkeypatch):
    captured = []

    def fake_run_command(*args):
        captured.append(args)
        return fake_result(*args)
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    force_stop_package(SERIAL, PACKAGE)

    assert captured[0] == (
        "adb",
        "-s",
        SERIAL,
        "shell",
        "am",
        "force-stop",
        PACKAGE,
    )

def test_force_stop_failure(monkeypatch):
    def fake_run_command(*args):
        return fake_result(
            *args,
            stderr="permission denied",
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    with pytest.raises(ActivityManagerError):
        force_stop_package(SERIAL, PACKAGE)


def test_get_process_ids(monkeypatch):
    def fake_run_command(*args):
        return fake_result(
            *args,
            stdout="12345 12346\n"
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    assert get_process_ids(SERIAL, PACKAGE) == [12345, 12346]

def test_get_process_ids_when_absent(monkeypatch):
    def fake_run_command(*args):
        return fake_result(
            *args,
            returncode=1,
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    assert get_process_ids(SERIAL, PACKAGE) == []


def test_pidof_error_is_not_silently_ignored(monkeypatch):
    def fake_run_command(*args):
        return fake_result(
            *args,
            stderr="device offline",
            returncode=1,
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    with pytest.raises(ActivityManagerError):
        get_process_ids(SERIAL, PACKAGE)

def test_is_process_running(monkeypatch):
    monkeypatch.setattr(
        am,
        "get_process_ids",
        lambda serial, package: [12345],
    )

    assert is_process_running(SERIAL, PACKAGE)

def test_get_activity_dump(monkeypatch):
    def fake_run_command(*args):
        return fake_result(
            *args,
            stdout="ACTIVITY MANAGER ACTIVITIES\n",
        )
    
    monkeypatch.setattr(
        am,
        "run_command",
        fake_run_command,
    )

    output = get_activity_dump(SERIAL)

    assert "ACTIVITY MANAGER" in output
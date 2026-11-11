import subprocess
from types import SimpleNamespace

import pytest

from android_cookbook import activity_launch_diagnostics as ald
from android_cookbook.activity_launch_diagnostics import (
    DisplayedEvent,
    LaunchError,
    LaunchObservation,
    LaunchType,
    assert_launch_type,
    parse_am_start_output,
    parse_displayed_events,
)

COLD_OUTPUT = """\
Status: ok
LaunchState: COLD
Activity: com.example.androidcookbook.fixture/.MainActivity
ThisTime: 320
TotalTime: 410
WaitTime: 435
Complete
"""

HOT_OUTPUT = """\
Status: ok
Activity: com.example.androidcookbook.fixture/.MainActivity
Warning: Activity not started, its current task has been brought to the front
Complete
"""


def make_observation(
    launch_type,
    pid_before,
    pid_after,
    instance_before,
    instance_after,
    created,
):

    return LaunchObservation(
        expected_type=launch_type,
        pid_before=pid_before,
        pid_after=pid_after,
        instance_before=instance_before,
        instance_after=instance_after,
        created_after_launch=created,
        result=parse_am_start_output(
            COLD_OUTPUT,
            host_elapsed_ms=500.0,
        ),
    )


def test_parse_cold_start_output():
    result = parse_am_start_output(
        COLD_OUTPUT,
        host_elapsed_ms=500.5,
    )

    assert result.status == "ok"
    assert result.launch_state == "COLD"
    assert result.this_time_ms == 320
    assert result.total_time_ms == 410
    assert result.wait_time_ms == 435
    assert result.host_elapsed_ms == 500.5


def test_parse_missing_timeing_fields():
    result = parse_am_start_output(
        HOT_OUTPUT,
        host_elapsed_ms=35.0,
    )

    assert result.this_time_ms is None
    assert result.total_time_ms is None
    assert result.wait_time_ms is None
    assert result.warning is not None


def test_parse_invalid_timing():
    with pytest.raises(
        LaunchError,
        match="Invalid TotalTime",
    ):
        parse_am_start_output(
            "Status: ok\nTotalTime: invalid",
            host_elapsed_ms=10,
        )


def test_cold_start_classification():
    observation = make_observation(
        LaunchType.COLD,
        None,
        1234,
        None,
        "instance-a",
        True,
    )

    assert_launch_type(observation)


def test_warm_start_classification():
    observation = make_observation(
        LaunchType.WARM,
        1234,
        1234,
        "instance-a",
        "instance-b",
        True,
    )

    assert_launch_type(observation)


def test_hot_start_classification():
    observation = make_observation(
        LaunchType.HOT,
        1234,
        1234,
        "instance-a",
        "instance-a",
        False,
    )

    assert_launch_type(observation)


@pytest.mark.parametrize(
    "observation",
    [
        make_observation(
            LaunchType.COLD,
            1234,
            1234,
            None,
            "b",
            True,
        ),
        make_observation(
            LaunchType.WARM,
            1234,
            5678,
            "a",
            "b",
            True,
        ),
        make_observation(
            LaunchType.WARM,
            1234,
            1234,
            "a",
            "a",
            False,
        ),
        make_observation(
            LaunchType.HOT,
            1234,
            1234,
            "a",
            "b",
            True,
        ),
    ],
)
def test_invalid_launch_classification(observation):
    with pytest.raises(AssertionError):
        assert_launch_type(observation)


def test_parse_displayed_events():
    output = (
        "I ActivityTaskManager: Displayed "
        "com.example.androidcookbook.fixture/.MainActivity: "
        "+1s234ms"
    )

    assert parse_displayed_events(output) == [
        DisplayedEvent(
            component=("com.example.androidcookbook.fixture/" ".MainActivity"),
            duration_ms=1234,
        )
    ]


def test_parse_displayed_without_seconds():
    output = "Displayed com.example.androidcookbook.fixture/" ".MainActivity: +410ms"

    events = parse_displayed_events(output)

    assert events[0].duration_ms == 410


def test_parse_displayed_ignores_unrelated_logs():
    assert parse_displayed_events("I ActivityManager: unrelated message") == []


def test_launch_activity_command_and_timing(monkeypatch):
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)

        return SimpleNamespace(
            returncode=0,
            stdout=COLD_OUTPUT,
            stderr="",
        )

    times = iter(
        [
            10.0,
            10.5,
        ]
    )

    monkeypatch.setattr(
        ald.subprocess,
        "run",
        fake_run,
    )
    monkeypatch.setattr(
        ald.time,
        "monotonic",
        lambda: next(times),
    )

    result = ald.launch_activity("emulator-5554")

    assert commands == [
        [
            "adb",
            "-s",
            "emulator-5554",
            "shell",
            "am",
            "start",
            "-W",
            "-n",
            ("com.example.androidcookbook.fixture/" ".MainActivity"),
        ]
    ]

    assert result.host_elapsed_ms == 500.0


def test_launch_activity_timeout(monkeypatch):

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(
            command,
            timeout=1,
        )

    monkeypatch.setattr(
        ald.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(LaunchError, match="timed out"):
        ald.launch_activity(
            "emulator-5554",
            timeout_seconds=1,
        )


def test_get_app_pid_absent(monkeypatch):
    monkeypatch.setattr(
        ald.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="",
        ),
    )

    assert ald.get_app_pid("emulator-5554") is None


def test_get_app_pid_present(monkeypatch):
    monkeypatch.setattr(
        ald.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="1234\n",
            stderr="",
        ),
    )

    assert ald.get_app_pid("emulator-5554") == 1234


def test_finish_fixture_activity(monkeypatch):
    calls = []

    monkeypatch.setattr(
        ald,
        "run_adb_command",
        lambda serial, *args: calls.append((serial, args)) or "",
    )

    ald.finish_fixture_activity("emulator-5554")

    assert "--activity-single-top" in calls[0][1]
    assert "cookbook_finish" in calls[0][1]
    assert "true" in calls[0][1]


@pytest.mark.parametrize(
    "outcomes, timeout, expected, expected_calls, expected_sleeps",
    [
        (
            [True],
            10.0,
            True,
            1,
            [],
        ),
        (
            [False, False, True],
            10.0,
            True,
            3,
            [0.2, 0.2],
        ),
        (
            [False],
            0.4,
            False,
            3,
            [0.2, 0.2],
        ),
        (
            [True],
            0.0,
            True,
            1,
            [],
        ),
        (
            [False],
            0.0,
            False,
            1,
            [],
        ),
    ],
)
def test_wait_until_polls_predicate(
    monkeypatch, outcomes, timeout, expected, expected_calls, expected_sleeps
):
    now = 0.0
    calls = []
    sleeps = []

    def predicate():
        index = min(len(calls), len(outcomes) - 1)
        calls.append(now)
        return outcomes[index]

    def sleep(seconds):
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    monkeypatch.setattr(ald.time, "monotonic", lambda: now)
    monkeypatch.setattr(ald.time, "sleep", sleep)

    assert ald.wait_until(predicate, timeout_seconds=timeout) is expected
    assert len(calls) == expected_calls
    assert sleeps == expected_sleeps


@pytest.mark.parametrize(
    "kwargs",
    [
        {"timeout_seconds": -1},
        {"poll_interval": 0},
        {"poll_interval": -0.1},
    ],
)
def test_wait_until_rejects_invalid_arguments(kwargs):
    def predicate():
        pytest.fail("Invalid arguments must be rejected before polling")

    with pytest.raises(ValueError):
        ald.wait_until(predicate, **kwargs)


def test_wait_until_propagates_predicate_error():
    def predicate():
        raise RuntimeError("PID lookup failed")

    with pytest.raises(RuntimeError, match="PID lookup failed"):
        ald.wait_until(predicate)

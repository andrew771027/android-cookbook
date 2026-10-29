import pytest

from android_cookbook import activity_lifecycle as lifecycle
from android_cookbook.activity_lifecycle import (
    LifecycleError,
    LifecycleEvent,
    contains_ordered_sequence,
    event_names,
    find_created_instance,
    parse_lifecycle_events,
    wait_for_lifecycle_sequence,
)

INSTANCE_A = "11111111-1111-1111-1111-111111111111"
INSTANCE_B = "22222222-2222-2222-2222-222222222222"


def log_line(instance: str, event: str) -> str:
    return (
        "10-19 10:00:00.000 1234 1234 I "
        "CookbookLifecycle: "
        "marker=android-cookbook-v0.5.2 "
        f"instance={instance} event={event}"
    )


def test_parse_lifecycle_events():
    output = "\n".join(
        [
            log_line(INSTANCE_A, "onCreate"),
            log_line(INSTANCE_A, "onStart"),
            log_line(INSTANCE_A, "onResume"),
        ]
    )

    assert parse_lifecycle_events(output) == [
        LifecycleEvent(INSTANCE_A, "onCreate"),
        LifecycleEvent(INSTANCE_A, "onStart"),
        LifecycleEvent(INSTANCE_A, "onResume"),
    ]


def test_parser_ignore_unrelated_logs():
    output = "\n".join(
        [
            "I OtherTag: event=onCreate",
            "I CookbookLifecycle: unrelated message",
            log_line(INSTANCE_A, "onResume"),
        ]
    )

    assert parse_lifecycle_events(output) == [
        LifecycleEvent(INSTANCE_A, "onResume"),
    ]


def test_parser_ignores_unknown_event():
    output = log_line(INSTANCE_A, "onUnknown")

    assert parse_lifecycle_events(output) == []


def test_parser_supports_multiple_instances():
    output = "\n".join(
        [
            log_line(INSTANCE_A, "onCreate"),
            log_line(INSTANCE_B, "onCreate"),
            log_line(INSTANCE_A, "onResume"),
        ]
    )

    events = parse_lifecycle_events(output)

    assert event_names(
        events,
        instance_id=INSTANCE_A,
    ) == [
        "onCreate",
        "onResume",
    ]


@pytest.mark.parametrize(
    ("actual", "expected", "result"),
    [
        (
            ["onCreate", "onStart", "onResume"],
            ["onCreate", "onStart", "onResume"],
            True,
        ),
        (
            ["onCreate", "onStart", "onResume", " onPause"],
            ["onCreate", "onResume"],
            True,
        ),
        (
            ["onResume", "onStart", "onCreate"],
            ["onCreate", "onStart", "onResume"],
            False,
        ),
        (
            ["onCreate", "onStart"],
            ["onCreate", "onStart", "onResume"],
            False,
        ),
        (
            [],
            ["onCreate"],
            False,
        ),
        (
            ["onCreate"],
            [],
            True,
        ),
    ],
)
def test_contains_ordered_swquence(
    actual,
    expected,
    result,
):

    assert (
        contains_ordered_sequence(
            actual,
            expected,
        )
        is result
    )


def test_find_created_instance():
    events = [
        LifecycleEvent(INSTANCE_A, "onCreate"),
        LifecycleEvent(INSTANCE_A, "onStart"),
    ]

    assert find_created_instance(events) == INSTANCE_A


def test_find_created_instance_missing():
    with pytest.raises(LifecycleError, match="No onCreate"):
        find_created_instance([])


def test_wait_for_lifecycle_sequence(monkeypatch):
    outputs = iter(
        [
            log_line(INSTANCE_A, "onCreate"),
            "\n".join(
                [
                    log_line(INSTANCE_A, "onCreate"),
                    log_line(INSTANCE_A, "onStart"),
                    log_line(INSTANCE_A, "onResume"),
                ]
            ),
        ]
    )

    monkeypatch.setattr(
        lifecycle,
        "read_lifecycle_logcat",
        lambda serial: next(outputs),
    )

    events = wait_for_lifecycle_sequence(
        "emulator-5554",
        [
            "onCreate",
            "onStart",
            "onResume",
        ],
        instance_id=INSTANCE_A,
        timeout_seconds=1,
        poll_interval=0.0001,
    )

    assert event_names(
        events,
        instance_id=INSTANCE_A,
    ) == [
        "onCreate",
        "onStart",
        "onResume",
    ]


def test_wait_for_lifecycle_timeout(monkeypatch):
    monkeypatch.setattr(
        lifecycle,
        "read_lifecycle_logcat",
        lambda serial: log_line(
            INSTANCE_A,
            "onCreate",
        ),
    )

    with pytest.raises(
        LifecycleError,
        match="not observed",
    ):
        wait_for_lifecycle_sequence(
            "emulator-5554",
            ["onCreate", "onStart", "onResume"],
            timeout_seconds=0,
        )


@pytest.mark.parametrize(
    "keycode",
    [
        "KEYCODE_HOME",
        "KEYCODE_BACK",
    ],
)
def test_send_keyevent(monkeypatch, keycode):
    calls = []

    def fake_run_adb(serial, *args, **kwargs):
        calls.append((serial, args))
        return ""

    monkeypatch.setattr(
        lifecycle,
        "run_adb_command",
        fake_run_adb,
    )

    lifecycle.send_keyevent(
        "emulator-5554",
        keycode,
    )

    assert calls == [
        (
            "emulator-5554",
            (
                "shell",
                "input",
                "keyevent",
                keycode,
            ),
        )
    ]


def test_invalid_keyevent():
    with pytest.raises(ValueError):
        lifecycle.send_keyevent(
            "emulator-5554",
            "KEYCODE_POWER",
        )


def test_request_activity_finish(monkeypatch):
    calls = []

    def fake_run_adb(serial, *args, **kwargs):
        calls.append((serial, args))
        return ""

    monkeypatch.setattr(
        lifecycle,
        "run_adb_command",
        fake_run_adb,
    )

    lifecycle.request_activity_finish(
        "emulator-5554",
    )

    assert calls == [
        (
            "emulator-5554",
            (
                "shell",
                "am",
                "start",
                "-W",
                "--activity-single-top",
                "-n",
                ("com.example.androidcookbook.fixture/" ".MainActivity"),
                "--ez",
                "cookbook_finish",
                "true",
            ),
        ),
    ]

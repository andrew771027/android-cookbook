import pytest

from android_cookbook import activity_recreation as ar
from android_cookbook.activity_recreation import (
    RotationSettings,
    StateEvent,
    assert_state_restored,
    capture_rotation_settings,
    parse_state_events,
    restore_rotation_settings,
    set_user_rotation,
)

INSTANCE_A = "11111111-1111-1111-1111-111111111111"
INSTANCE_B = "22222222-2222-2222-2222-222222222222"


def state_line(
    instance,
    event,
    counter,
    orientation,
    restored,
):

    return (
        "10-27 11:00:00.000 1234 1234 I CookbookState: "
        "marker=android-cookbook-v0.5.2 "
        f"instance={instance} "
        f"event={event} "
        f"counter={counter} "
        f"orientation={orientation} "
        f"restored={str(restored).lower()}"
    )


def test_parse_state_events():

    output = "\n".join(
        [
            state_line(INSTANCE_A, "saved", 5, "portrait", False),
            state_line(INSTANCE_B, "created", 5, "landscape", True),
        ]
    )

    assert parse_state_events(output) == [
        StateEvent(INSTANCE_A, "saved", 5, "portrait", False),
        StateEvent(INSTANCE_B, "created", 5, "landscape", True),
    ]


def test_parser_ignores_unrelated_logs():
    output = "\n".join(
        [
            "I OtherTag: unrelated",
            state_line(INSTANCE_A, "created", 0, "portrait", False),
        ]
    )

    assert len(parse_state_events(output)) == 1


def test_state_restoration_success():
    before = StateEvent(INSTANCE_A, "incremented", 5, "portrait", False)

    after = StateEvent(INSTANCE_B, "created", 5, "landscape", True)

    assert_state_restored(before, after)


@pytest.mark.parametrize(
    "after",
    [
        StateEvent(INSTANCE_A, "created", 5, "landscape", True),
        StateEvent(INSTANCE_B, "created", 0, "landscape", True),
        StateEvent(INSTANCE_B, "created", 5, "landscape", False),
        StateEvent(INSTANCE_B, "created", 5, "portrait", True),
    ],
)
def test_state_restoration_failures(after):
    before = StateEvent(INSTANCE_A, "incremented", 5, "portrait", False)

    with pytest.raises(AssertionError):
        assert_state_restored(before, after)


def test_set_user_rotation(monkeypatch):
    calls = []

    monkeypatch.setattr(
        ar,
        "run_adb_command",
        lambda serial, *args: calls.append((serial, args)) or "",
    )

    set_user_rotation("emulator-5554", 1)

    assert calls == [
        (
            "emulator-5554",
            (
                "shell",
                "settings",
                "put",
                "system",
                "accelerometer_rotation",
                "0",
            ),
        ),
        (
            "emulator-5554",
            (
                "shell",
                "settings",
                "put",
                "system",
                "user_rotation",
                "1",
            ),
        ),
    ]


def test_invalid_rotation():
    with pytest.raises(ValueError):
        set_user_rotation("emulator-5554", 4)


def test_capture_rotation_settings(monkeypatch):
    values = {
        "accelerometer_rotation": "1",
        "user_rotation": "0",
    }

    monkeypatch.setattr(
        ar,
        "get_system_setting",
        lambda serial, key: values[key],
    )

    assert capture_rotation_settings("emulator-5554") == RotationSettings("1", "0")


def test_restore_rotation_settings(monkeypatch):
    calls = []

    monkeypatch.setattr(
        ar,
        "put_system_setting",
        lambda serial, key, value: calls.append(("put", key, value)),
    )

    monkeypatch.setattr(
        ar,
        "delete_system_setting",
        lambda serial, key: calls.append(("delete", key)),
    )

    restore_rotation_settings(
        "emulator-5554",
        RotationSettings("1", None),
    )

    assert calls == [
        ("delete", "user_rotation"),
        ("put", "accelerometer_rotation", "1"),
    ]


def test_wait_for_state_event(monkeypatch):
    events = iter(
        [
            [],
            [StateEvent(INSTANCE_A, "created", 0, "portrait", False)],
        ]
    )

    monkeypatch.setattr(
        ar,
        "read_state_events",
        lambda serial: next(events),
    )

    event = ar.wait_for_state_event(
        "emulator-5554",
        lambda e: e.name == "created",
        timeout_seconds=1,
        poll_interval=0.001,
    )

    assert event.instance_id == INSTANCE_A


def test_wait_for_state_event_timeout(monkeypatch):
    monkeypatch.setattr(
        ar,
        "read_state_events",
        lambda serial: [],
    )

    with pytest.raises(ar.LifecycleError, match="Timed out"):
        ar.wait_for_state_event(
            "emulator-5554",
            lambda e: e.name == "created",
            timeout_seconds=0,
        )


def test_send_fixture_action(monkeypatch):
    calls = []

    monkeypatch.setattr(
        ar,
        "run_adb_command",
        lambda serial, *args: calls.append((serial, args)) or "",
    )

    ar.send_fixture_action("emulator-5554", "increment")

    assert calls[0][1][-3:] == (
        "--es",
        "cookbook_action",
        "increment",
    )

import pytest

from android_cookbook import process_recovery as pr
from android_cookbook.process_recovery import (
    ProcessStateEvent,
    assert_state_recovered,
    evaluate_recovery,
    parse_process_state_events,
    wait_for_new_process,
    wait_for_process_absent,
)


INSTANCE_A = "11111111-1111-1111-1111-111111111111"
INSTANCE_B = "22222222-2222-2222-2222-222222222222"

def make_event(
    instance=INSTANCE_A,
    event="created",
    counter=5,
    orientation=False,
    restored=False,
    pid=1234,
):

    return ProcessStateEvent(
        instance_id=instance,
        name=event,
        counter=counter,
        orientation="portrait",
        restored=restored,
        pid=pid,
    )

def log_line(
    instance=INSTANCE_A,
    event="created",
    counter=5,
    restored=False,
    pid=1234,
):

    return (
        "11-01 15:00:00.000 1234 1234 I CookbookState: "
        "marker=android-cookbook-v0.5.2 "
        f"instance={instance} "
        f"event={event} "
        f"counter={counter} "
        "orientation=portrait "
        f"restored={str(restored).lower()} "
        f"pid={pid}"
    )

def test_parse_process_state_event():
    events = parse_process_state_events(log_line())

    assert events == [make_event()]

def test_parse_multiple_processes():
    output = "\n".join([
        log_line(pid=1234),
        log_line(
            instance=INSTANCE_B,
            pid=5678,
            restored=True,
        ),
    ])

    events = parse_process_state_events(output)

    assert [event.pid for event in events] == [
        1234,
        5678,
    ]


def test_parser_ignores_unrelated_logs():
    assert parse_process_state_events(
        "I OtherTag unrelated"
    ) == []


def test_wait_for_process_absent(monkeypatch):
    responses = iter([[1234], []])

    monkeypatch.setattr(
        pr,
        "get_process_ids",
        lambda serial, package: next(responses),
    )

    assert wait_for_process_absent(
        "emulator-5554",
        timeout_seconds=1,
    )

def test_wait_for_process_absent_timeout(monkeypatch):
    monkeypatch.setattr(
        pr,
        "get_process_ids",
        lambda serial, package: [1234],
    )

    assert not wait_for_process_absent(
        "emulator-5554",
        timeout_seconds=0,
    )

def test_wait_for_new_process(monkeypatch):
    responses = iter([
        [],
        [5678],
    ])

    monkeypatch.setattr(
        pr,
        "get_process_ids",
        lambda serial, package: next(responses),
    )

    assert wait_for_new_process(
        "emulator-5554",
        old_pid=1234,
        timeout_seconds=1,
    ) == 5678

def test_evaluate_recovery():
    before = make_event(pid=1234)

    after = make_event(
        instance=INSTANCE_B,
        pid=5678,
        restored=True,
    )

    result = evaluate_recovery(before, after)

    assert result.old_pid == 1234
    assert result.new_pid == 5678
    assert result.old_counter == 5
    assert result.new_counter == 5

    assert_state_recovered(result)

def test_recovery_without_saved_state():
    before = make_event(pid=1234)

    after = make_event(
        instance=INSTANCE_B,
        pid=5678,
        counter=0,
        restored=False,
    )

    result = evaluate_recovery(before, after)

    with pytest.raises(AssertionError, match="savedInstanceState",):
        assert_state_recovered(result)

def test_recovery_with_wrong_counter():
    before = make_event(pid=1234)

    after make_event(
        instance=INSTANCE_B,
        pid=5678,
        counter=0,
        restored=True,
    )

    result = evaluate_recovery(before, after)

    with pytest.raises(AssertionError, match="Counter was not restored",):
        assert_state_recovered(result)

@pytest.mark.parameterize(
    "after",
    [
        make_event(instance=INSTANCE_B, pid=1234,),
        make_event(instance=INSTANCE_A, pid=5678,),
        make_event(instance=INSTANCE_B, pid=5678, event="resumed",),
    ],
)
def test_invalid_recovery_identity(after):
    with pytest.raises(AssertionError):
        evaluate_recovery(
            make_event(pid=1234),
            after,
        )

def test_request_background_process_kill(monkeypatch):
    calls = []

    monkeypatch.setattr(
        pr,
        "run_adb_command",
        lambda serial, *args: calls.append((serial, args)) or "", 
    )

    pr.requset_background_process_kill(
        "emulator-5554",
    )

    assert calls == [
        (
            "emulator-5554",
            (
                "shell",
                "am",
                "kill",
                pr.PACKAGE,
            ),
        )
    ]

def test_launch_from_launcher(monkeypatch):
    calls = []

    monkeypatch.setattr(
        pr,
        "run_adb_command",
        lambda serial, *args: calls.append((serial, args)) or "Status: ok",
    )

    output = pr.launch_from_launcher("emulator-5554")

    assert "Status: ok" in output
    assert "android.intent.action.MAIN" in calls[0][1]
    assert "android.intent.category.LAUNCHER" in calls[0][1]
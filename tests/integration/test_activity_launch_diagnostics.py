import pytest

from android_cookbook.activity_lifecycle import (
    clear_logcat,
    parse_lifecycle_events,
    press_home,
    read_lifecycle_logcat,
    wait_for_lifecycle_sequence,
)
from android_cookbook.activity_launch_diagnostics import(
    LaunchObservation,
    LaunchType,
    assert_launch_type,
    finish_fixture_activity,
    force_stop_app,
    get_app_pid,
    launch_activity,
    wait_until,
)
from android_cookbook.activity_recreation import (
    wait_for_state_event,
    send_fixture_action,
)
from android_cookbook.package_manager import (
    install_apk,
    package_exists,
)

PACKAGE = "com.example.androidcookbook.fixture"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]

@pytest.fixture
def launch_app(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    result = install_apk(
        android_serial,
        test_apk,
        allow_test_packages=True,
    )

    assert "Success" in result
    assert package_exists(
        android_serial,
        package_name,
    )

    force_stop_app(android_serial)
    clear_logcat(android_serial)

    return package_name

def latest_created_instance(serial):
    events = parse_lifecycle_events(
        read_lifecycle_logcat(serial)
    )

    created = [
        event.instance_id
        for event in events
        if event.name == "onCreate"
    ]

    assert created, "No onCreate event observed"

    return created[-1]

def lifecycle_names(serial, instance_id):
    events = parse_lifecycle_events(
        read_lifecycle_logcat(serial)
    )

    return [
        event.name
        for event in events
        if event.instance_id == instance_id
    ]


def test_cold_start(
    android_serial,
    launch_app,
):

    # Force-stop is used only to establish a clean
    # no-process cold-start precondition.
    force_stop_app(android_serial)

    assert wait_until(
        lambda: get_app_pid(android_serial) is None
    )

    pid_before = get_app_pid(android_serial)

    clear_logcat(android_serial)

    result = launch_activity(android_serial)

    created = wait_for_state_event(
        android_serial,
        lambda e: e.name == "created",
    )

    pid_after = get_app_pid(android_serial)

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onCreate",
            "onStart",
            "onResume",
        ],
        install_apk=created.instance_id,
    )

    observation = LaunchObservation(
        expected_type=LaunchType.COLD,
        pid_before=pid_before,
        pid_after=pid_after,
        instance_before=None,
        instance_after=created.instance_id,
        create_after_launch=True,
        result=result,
    )

    assert_launch_type(observation)

    assert created.counter == 0
    assert not created.restored

    print(
        f"Cold start: "
        f"TotalTime={result.total_time_ms}ms, "
        f"HostElapsed={result.host_elapsed_ms:.1f}ms"
    )

def test_warm_start(
    android_serial,
    launch_app,
):

    # 1. Launch the first Activity.
    launch_app(android_serial)

    first = wait_for_state_event(
        android_serial,
        lambda e: e.name == "created",
    )

    old_instance = first.instance_id
    old_pid = get_app_pid(android_serial)

    assert old_pid is not None

    # 2. Gracefully finish the Activity.
    finish_fixture_activity(android_serial)

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onDestroy"
        ],
        instance_id=old_instance,
    )

    # 3. Confirm the process survived.
    pid_before = get_app_pid(android_serial)

    if pid_before != old_pid:
        pytest.skip(
            "Process did not survive Activity finish; "
            "warm-start precondition unavailable"
        )

    # 4. Clear only the dedicagted emulator's logs.
    clear_logcat(android_serial)

    # 5. Launch again.
    result = launch_activity(android_serial)

    new_instance = wait_for_state_event(
        android_serial,
        lambda e: (
            e.name == "created"
            and e.instance_id != old_instance
        ),
    )

    pid_after = get_app_pid(android_serial)

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onCreate",
            "onStart",
            "onResume",
        ],
        instance_id=new_instance.instance_id,
    )

    observation = LaunchObservation(
        expected_type=LaunchType.WARM,
        pid_before=pid_before,
        pid_after=pid_after,
        instance_before=old_instance,
        instance_after=new_instance.instance_id,
        create_after_launch=True,
        result=result,
    )

    assert_launch_type(observation)

    print(
        f"Warm start: "
        f"TotalTime={result.total_time_ms}ms, "
        f"HostElapsed={result.host_elapsed_ms:.1f}ms"
    )


def test_hot_start(
    android_serial,
    launch_app,
):

    # 1. Launch Activity.
    launch_activity(android_serial)

    first = wait_for_state_event(
        android_serial,
        lambda e: e.name == "created",
    )

    instance_id = first.instance_id
    original_pid = get_app_pid(android_serial)

    assert original_pid is not None

    # 2. Move the Activity to background.
    press_home(android_serial)

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onPause",
            "onStop"
        ],
        instance_id=instance_id,
    )

    pid_before = get_app_pid(android_serial)

    if pid_before != original_pid:
        pytest.skip(
            "Process disappeared before hot-start test"
        )
    
    # 3. Isolate the launch observation window.
    clear_logcat(android_serial)

    # 4. Bring the existing Activity to foreground.
    result = launch_activity(android_serial)

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onRestart",
            "onStart",
            "onResume",
        ],
        instance_id=instance_id,
    )

    pid_after = get_app_pid(android_serial)

    events = parse_lifecycle_events(
        read_lifecycle_logcat(android_serial)
    )

    create_after_launch = any(
        event.name == "onCreate"
        for event in events
    )

    observation = LaunchObservation(
        expected_type=LaunchType.HOT,
        pid_before=pid_before,
        pid_after=pid_after,
        instance_before=instance_id,
        instance_after=instance_id,
        create_after_launch=create_after_launch,
        result=result,
    )

    assert_launch_type(observation)

    print(
        f"Hot start: "
        f"TotalTime={result.total_time_ms}ms, "
        f"HostElapsed={result.host_elapsed_ms:.1f}ms"
    )

    send_fixture_action(android_serial, "report")

    reported = wait_for_state_event(
        android_serial,
        lambda e: e.name == "reported",
    )

    assert reported.instance_id == instance_id
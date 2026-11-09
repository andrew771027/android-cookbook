import pytest

from android_cookbook.activity_lifecycle import (
    clear_logcat,
    press_home,
)
from android_cookbook.activity_manager import (
    force_stop_package,
    get_process_ids,
    start_activity,
)
from android_cookbook.activity_recreation import (
    send_fixture_action,
)
from android_cookbook.package_manager import (
    install_apk,
    package_exists,
)
from android_cookbook.process_recovery import (
    ACTIVITY,
    PACKAGE,
    assert_state_recovered,
    evaluate_recovery,
    launch_from_launcher,
    request_background_process_kill,
    wait_for_process_absent,
    wait_for_process_state_event,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]


@pytest.fixture
def recovery_app(
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

    clear_logcat(android_serial)

    return package_name


def prepare_background_app(
    serial: str,
    package_name: str,
    *,
    counter: int = 5,
):

    # 1. Launch fresh Activity.
    force_stop_package(serial, package_name)

    launch_from_launcher(
        serial,
        package_name,
        ACTIVITY,
    )

    created = wait_for_process_state_event(
        serial,
        lambda e: (e.name == "created" and e.counter == 0 and not e.restored),
    )

    # 2. Modify the Activity state.
    for expected in range(1, counter + 1):
        send_fixture_action(serial, "increment")

        wait_for_process_state_event(
            serial,
            lambda e, n=expected: (
                e.instance_id == created.instance_id and e.name == "incremented" and e.counter == n
            ),
        )

    # 3. Background the Activity.
    press_home(serial)

    # 4. Verify saved state exists.
    saved = wait_for_process_state_event(
        serial,
        lambda e: (
            e.instance_id == created.instance_id and e.name == "saved" and e.counter == counter
        ),
    )

    return saved


def kill_background_app(
    serial: str,
    old_pid: int,
):

    request_background_process_kill(serial)

    killed = wait_for_process_absent(
        serial,
        timeout_seconds=10,
    )

    if not killed:
        pytest.skip(
            "am kill did not terminate the background process. "
            "Android may still consider the process important."
        )

    assert old_pid not in get_process_ids(
        serial,
        PACKAGE,
    )


def test_background_process_death(
    android_serial,
    recovery_app,
):

    before = prepare_background_app(
        android_serial,
        recovery_app,
    )

    old_pid = before.pid

    kill_background_app(
        android_serial,
        old_pid,
    )

    assert not get_process_ids(
        android_serial,
        recovery_app,
    )

    # Process death does not uninstall the package.
    assert package_exists(
        android_serial,
        recovery_app,
    )


def test_process_death_state_recovery(
    android_serial,
    recovery_app,
):

    # 1. Prepare Activity with counter=5.
    before = prepare_background_app(
        android_serial,
        recovery_app,
        counter=5,
    )

    # 2. Confirm the original process is gone.
    kill_background_app(
        android_serial,
        before.pid,
    )

    # 3. Relaunch via MAIN/LAUNCHER intent.
    launch_from_launcher(
        android_serial,
        recovery_app,
        ACTIVITY,
    )

    # 4. Observe a newly created Activity.
    after = wait_for_process_state_event(
        android_serial,
        lambda e: (
            e.name == "created" and e.pid != before.pid and e.instance_id != before.instance_id
        ),
    )

    # 5. Validate process and instance identities.
    result = evaluate_recovery(before, after)

    assert result.old_pid != result.new_pid
    assert result.old_instance_id != result.new_instance_id

    # 6. Validate Bundle recovery.
    assert_state_recovered(result)

    # 7. Package must still be installed.
    assert package_exists(
        android_serial,
        recovery_app,
    )


def test_force_stop_does_not_unstall_package(
    android_serial,
    recovery_app,
):

    result = start_activity(
        android_serial,
        recovery_app,
        ACTIVITY,
        force_stop_before_start=True,
    )

    assert result.success

    force_stop_package(
        android_serial,
        recovery_app,
    )

    assert wait_for_process_absent(
        android_serial,
        recovery_app,
    )

    assert wait_for_process_absent(
        android_serial,
        recovery_app,
    )

    assert package_exists(
        android_serial,
        recovery_app,
    )

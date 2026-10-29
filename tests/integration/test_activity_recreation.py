import pytest

from android_cookbook.activity_lifecycle import (
    clear_logcat,
    wait_for_lifecycle_sequence,
)
from android_cookbook.activity_manager import start_activity
from android_cookbook.activity_recreation import (
    assert_state_restored,
    send_fixture_action,
    set_user_rotation,
    wait_for_state_event,
)
from android_cookbook.package_manager import (
    install_apk,
    package_exists,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]

PACKAGE = "com.example.androidcookbook.fixture"
ACTIVITY = ".MainActivity"


@pytest.fixture
def recreation_app(
    android_serial,
    test_apk,
    clean_test_package,
    controlled_rotation,
):

    package_name = clean_test_package

    result = install_apk(
        android_serial,
        test_apk,
        allow_test_packages=True,
    )

    assert "Success" in result
    assert package_exists(android_serial, package_name)

    clear_logcat(android_serial)

    return package_name


def test_rotation_recreates_activity_and_restores_state(
    android_serial,
    recreation_app,
):

    # 1. Launch a fresh Activity.
    result = start_activity(
        android_serial,
        recreation_app,
        ACTIVITY,
        force_stop_before_start=True,
    )

    assert result.success

    original = wait_for_state_event(
        android_serial,
        lambda e: (
            e.name == "created"
            and e.counter == 0
            and e.orientation == "portrait"
            and not e.restored
        ),
    )

    instance_a = original.instance_id

    # 2. Increment state five times.
    for counter in range(1, 6):
        send_fixture_action(
            android_serial,
            "increment",
        )

        wait_for_state_event(
            android_serial,
            lambda e, expected=counter: (
                e.instance_id == instance_a and e.name == "incremented" and e.counter == expected
            ),
        )

    before = wait_for_state_event(
        android_serial,
        lambda e: (e.instance_id == instance_a and e.name == "incremented" and e.counter == 5),
    )

    # 3. Rotate to landscape.
    set_user_rotation(android_serial, 1)

    # 4. Observe state saving on the old instance.
    saved = wait_for_state_event(
        android_serial,
        lambda e: (e.instance_id == instance_a and e.name == "saved" and e.counter == 5),
    )

    assert saved.counter == 5

    # 5. Validate restoration
    after = wait_for_state_event(
        android_serial,
        lambda e: (e.instance_id != instance_a and e.orientation == "landscape"),
    )

    # 6. Validate resotration
    assert_state_restored(before, after)

    # 7. Validate lifecycle callbacks per instance.
    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onPause",
            "onStop",
            "onDestroy",
        ],
        instance_id=instance_a,
    )

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onCreate",
            "onStart",
            "onResume",
        ],
        instance_id=after.instance_id,
    )

    # 8. Confirm package still installed.
    assert package_exists(
        android_serial,
        recreation_app,
    )


def test_rotation_does_not_uninstall_package(
    android_serial,
    recreation_app,
):
    start_activity(
        android_serial,
        recreation_app,
        ACTIVITY,
        force_stop_before_start=True,
    )

    original = wait_for_state_event(
        android_serial,
        lambda e: (e.name == "created" and e.orientation == "portrait"),
    )

    set_user_rotation(android_serial, 1)

    recreated = wait_for_state_event(
        android_serial,
        lambda e: (
            e.name == "created"
            and e.instance_id != original.instance_id
            and e.orientation == "landscape"
        ),
    )

    assert recreated.instance_id != original.instance_id

    assert package_exists(
        android_serial,
        recreation_app,
    )

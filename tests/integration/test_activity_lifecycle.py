import pytest

from android_cookbook.activity_lifecycle import (
    ACTIVITY,
    clear_logcat,
    event_names,
    find_created_instance,
    press_home,
    request_activity_finish,
    wait_for_lifecycle_sequence,
)
from android_cookbook.activity_manager import start_activity
from android_cookbook.package_manager import (
    install_apk,
    package_exists,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]


@pytest.fixture
def lifecycle_app(
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

    # Dedicated emulator only.
    clear_logcat(android_serial)

    return package_name


def launch_and_observe(
    serial: str,
    package_name: str,
):

    result = start_activity(
        serial,
        package_name,
        ACTIVITY,
        force_stop_before_start=True,
    )

    assert result.success

    events = wait_for_lifecycle_sequence(
        serial,
        [
            "onCreate",
            "onStart",
            "onResume",
        ],
    )

    instance_id = find_created_instance(events)

    return instance_id


def test_activity_luanch_lifecycle(
    android_serial,
    lifecycle_app,
):

    instance_id = launch_and_observe(
        android_serial,
        lifecycle_app,
    )

    events = wait_for_lifecycle_sequence(
        android_serial,
        [
            "onCreate",
            "onStart",
            "onResume",
        ],
        instance_id=instance_id,
    )

    assert event_names(events, instance_id=instance_id)[:3] == [
        "onCreate",
        "onStart",
        "onResume",
    ]


def test_home_triggers_pause_and_stop(
    android_serial,
    lifecycle_app,
):
    instance_id = launch_and_observe(
        android_serial,
        lifecycle_app,
    )

    press_home(android_serial)

    events = wait_for_lifecycle_sequence(
        android_serial,
        [
            "onCreate",
            "onStart",
            "onResume",
            "onPause",
            "onStop",
        ],
        instance_id=instance_id,
    )

    assert "onStop" in event_names(
        events,
        instance_id=instance_id,
    )


def test_return_from_home(
    android_serial,
    lifecycle_app,
):
    instance_id = launch_and_observe(
        android_serial,
        lifecycle_app,
    )

    press_home(android_serial)

    wait_for_lifecycle_sequence(
        android_serial,
        [
            "onPause",
            "onStop",
        ],
        instance_id=instance_id,
    )

    result = start_activity(
        android_serial,
        lifecycle_app,
        ACTIVITY,
    )

    assert result.success

    events = wait_for_lifecycle_sequence(
        android_serial,
        [
            "onRestart",
            "onStart",
            "onResume",
        ],
        instance_id=instance_id,
    )

    names = event_names(
        events,
        instance_id=instance_id,
    )

    assert names.count("onCreate") == 1
    assert "onRestart" in names


def test_graceful_finish_triggers_destroy(
    android_serial,
    lifecycle_app,
):

    instance_id = launch_and_observe(
        android_serial,
        lifecycle_app,
    )

    request_activity_finish(
        android_serial,
        lifecycle_app,
    )

    events = wait_for_lifecycle_sequence(
        android_serial,
        ["onPause", "onStop", "onDestroy"],
        instance_id=instance_id,
    )

    names = event_names(
        events,
        instance_id=instance_id,
    )

    assert "onDestroy" in names

    # Finishing an Activity does not uninstall the APK.
    assert package_exists(
        android_serial,
        lifecycle_app,
    )

import time
import pytest

from android_cookbook.activity_manager import (force_stop_package, get_activity_dump, get_process_ids, is_process_running, start_activity,)

from android_cookbook.package_manager import (install_apk, package_exists,)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]

ACTIVITY = ".MainActivity"

def wait_for_process_state(
    serial: str,
    package_name: str,
    *,
    expected_running: bool,
    timeout_seconds: float = 10.0,
    poll_interval: float = 0.2,
) -> bool:

    deadline = time.monotonic() + timeout_seconds

    while True:

        running = is_process_running(
            serial,
            package_name,
        )

        if running == expected_running:
            return True
        
        if time.monotonic() >= deadline:
            return False
        
        time.sleep(poll_interval)

@pytest.fixture
def installed_fixture(android_serial, test_apk, clean_test_package,):

    package_name = clean_test_package

    result = install_apk(
        android_serial,
        test_apk,
        allow_test_packages=True,
    )

    assert "Success" in result
    assert package_exists(android_serial, package_name)

    return package_name

def test_start_activity(android_serial, installed_fixture,):

    result = start_activity(
        android_serial,
        installed_fixture,
        ACTIVITY,
    )

    assert result.success
    assert result.status == "ok"

def test_start_activity_creates_process(android_serial, installed_fixture,):

    start_activity(
        android_serial,
        installed_fixture,
        ACTIVITY,
    )

    assert wait_for_process_state(
        android_serial,
        installed_fixture,
        expected_running=True,
    )

    assert get_process_ids(
        android_serial,
        installed_fixture,
    )

def test_force_stop_terminates_process(android_serial, installed_fixture,):

    start_activity(
        android_serial,
        installed_fixture,
        ACTIVITY,
    )

    assert wait_for_process_state(
        android_serial,
        installed_fixture,
        expected_running=True,
    )

    force_stop_package(
        android_serial,
        installed_fixture,
    )

    assert wait_for_process_state(
        android_serial,
        installed_fixture,
        expected_running=False,
    )

    # Force-stop does not uninstall the package.
    assert package_exists(android_serial, installed_fixture,)

def test_restart_activity_after_force_stop(android_serial, installed_fixture,):

    first = start_activity(
        android_serial,
        installed_fixture,
        ACTIVITY,
    )

    assert first.success

    force_stop_package(
        android_serial,
        installed_fixture,
    )

    assert wait_for_process_state(
        android_serial,
        installed_fixture,
        expected_running=False,
    )

    second = start_activity(
        android_serial,
        installed_fixture,
        ACTIVITY,
        force_stop_before_start=True,
    )

    assert second.success

    assert wait_for_process_state(
        android_serial,
        installed_fixture,
        expected_running=True,
    )

def test_activity_dump_available(android_serial, installed_fixture,)

    start_activity(
        android_serial,
        installed_fixture,
        ACTIVITY,
    )

    output = get_activity_dump(android_serial)

    assert output.strip()
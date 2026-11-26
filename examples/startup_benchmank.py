import argparse
from pathlib import Path

from android_cookbook.activity_lifecycle import (
    LifecycleError,
    clear_logcat,
    press_home,
    wait_for_lifecycle_sequence,
)

from android_cookbook.activity_launch_diagnostics import (
    LaunchError,
    LaunchObservation,
    LaunchType,
    finish_fixture_activity,
    force_stop_app,
    get_app_pid,
    launch_activity,
    wait_until,
)

from android_cookbook.process_recovery import (
    read_process_state_events,
    wait_for_process_state_event,
)

from android_cookbook.activity_recreation import (
    send_fixture_action,
)

from android_cookbook.startup_performance import (
    BenchmarkConfig,
    InvalidScenarioError,
    run_benchmark,
)

from android_cookbook.startup_artifacts import (
    collect_environment,
    create_artifact_directory,
    write_artifacts,
)

def execute_experiment(
    serial: str,
    launch_type: LaunchType,
) -> LaunchObservation:

    try:

        return _execute_experiment(
            serial,
            launch_type,
        )

    except LifecycleError as exc:
        raise InvalidScenarioError(
            f"Lifecycle observation failed: {exc}"
        ) from exc

def _execute_experiment(serial: str, launch_type: LaunchType,) -> LaunchObservation:

    # Rest the previous experiment.
    force_stop_app(serial)

    if not wait_until(lambda: get_app_pid(serial) is None):
        raise InvalidScenarioError(
            "Previous process did not stop"
        )
    
    clear_logcat(serial)

    instance_before = None

    # Prepare warm or hot startup
    if launch_type != LaunchType.COLD:
        launch_activity(serial)

        initial = wait_for_process_state_event(
            serial,
            lambda event: event.name == "created",
        )

        instance_before = initial.instance_id

        wait_for_lifecycle_sequence(
            serial,
            [
                "onCreate",
                "onStart",
                "onResume",
            ],
            instance_id=instance_before,
        )

        original_pid = get_app_pid(serial)

        if original_pid is None:
            raise InvalidScenarioError(
                "Initial process not found"
            )

        if launch_type == LaunchType.WARM:
            finish_fixture_activity(serial)

            wait_for_lifecycle_sequence(
                serial,
                [
                    "onDestroy",
                ],
                instance_id=instance_before,
            )

        elif launch_type == LaunchType.HOT:
            press_home(serial)

            wait_for_lifecycle_sequence(
                serial,
                [
                    "onPause",
                    "onStop"
                ],
                instance_id=instance_before,
            )

        if get_app_pid(serial) != original_pid:
            raise InvalidScenarioError(
                "Process disappeared during setup"
            )

    # Isolate the measurement window
    clear_logcat(serial)

    pid_before = get_app_pid(serial)

    if launch_type == LaunchType.COLD and pid_before is not None:
        raise InvalidScenarioError(
            "Cold-start process already exists"
        )

    if launch_type != LaunchType.COLD and pid_before is None:
        raise InvalidScenarioError(
            "Required process no longer exists"
        )

    # Only this launch is measured
    result = launch_activity(serial)

    # Observe actual Activity identity.
    if launch_type == LaunchType.HOT:

        wait_for_lifecycle_sequence(
            serial,
            [
                "onRestart",
                "onStart",
                "onResume",
            ],
            instance_id=instance_before,
        )

        # Report action is outside the timed window.
        send_fixture_action(serial, "report")

        observed = wait_for_process_state_event(
            serial,
            lambda event: event.name == "reported",
        )

    else:
        observed = wait_for_process_state_event(
            serial,
            lambda event: event.name == "created",
        )

        wait_for_lifecycle_sequence(
            serial,
            [
                "onCreate",
                "onStart",
                "onResume",
            ],
            instance_id=observed.instance_id,
        )

    events = read_process_state_events(serial)

    created_after_launch = any(event.name == "created" for event in events)

    pid_after = get_app_pid(serial)

    if pid_after != observed.pid:
        raise InvalidScenarioError(
            "Observed Activity PID does not match current process"
        )

    return LaunchObservation(
        expected_type=launch_type,
        pid_before=pid_before,
        pid_after=pid_after,
        instance_before=instance_before,
        instance_after=observed.instance_id,
        created_after_launch=created_after_launch,
        result=result,
    )

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Android startup benchmark"
    )

    parser.add_argument(
        "--serial",
        required=True,
    )

    parser.add_argument(
        "--type",
        choices=["cold", "warm", "hot",],
        required=True,
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/startup"),
    )

    args = parser.parse_args()

    if not args.serial.startswith("emulator-"):
        parser.error(
            "Use a dedicated Android Emulator"
        )

    config = BenchmarkConfig(
        launch_type=LaunchType(args.type),
        iterations=args.iterations,
        warmup_runs=args.warmup,
        interval_seconds=args.interval,
    )

    environment = collect_environment(args.serial)

    directory = create_artifact_directory(args.output, config.launch_type.value,)

    try:

        result = run_benchmark(
            config,
            experiment=lambda launch_type : (execute_experiment(args.serial, launch_type,),)
        )

        write_artifacts(
            result=result,
            directory=directory,
            environment=environment,
        )

        summary = result.summary

        print(f"Artifacts: {directory}")
        print(f"Scenario: {summary.launch_type.value}")
        print(f"Success: {summary.successful_runs}")
        print(f"Failed: {summary.failed_runs}")
        print(f"Invalid: {summary.invalid_runs}")
        print(f"Mean: {summary.total_time.mean}")
        print(f"Median: {summary.total_time.median}")
        print(f"P95: {summary.total_time.p95}")

        return 0 if summary.successful_runs == config.interval_seconds else 1

    finally:
        force_stop_app(args.serial)

if __name__ == "__main__":
    raise SystemExit(main())
import pytest

from android_cookbook.activity_launch_diagnostics import (
    LaunchError,
    LaunchResult,
    LaunchType,
)
from android_cookbook.startup_performance import (
    BenchmarkConfig,
    InvalidScenarioError,
    RunStatus,
    run_benchmark,
)


def make_observation(
    total_time=400,
    launch_type=LaunchType.COLD,
):
    result = LaunchResult(
        status="ok",
        launch_state=launch_type.value.upper(),
        activity="example/.MainActivity",
        this_time_ms=None,
        total_time_ms=total_time,
        wait_time_ms=450,
        host_elapsed_ms=500.0,
        warning=None,
        raw_output="Status: ok",
    )

    return LaunchResult(
        expected_type=launch_type,
        pid_before=None,
        pid_after=1234,
        instance_before=None,
        instance_after="instance-a",
        created_after_launch=True,
        result=result,
    )


def make_config(
    iterations=3,
    warmup_runs=0,
):
    return BenchmarkConfig(
        launch_type=LaunchType.COLD,
        iterations=iterations,
        warmup_runs=warmup_runs,
        interval_seconds=0,
    )


def test_repeated_runs():
    values = iter(
        [
            300,
            400,
            500,
        ]
    )

    result = run_benchmark(
        make_config(),
        experiment=lambda _: make_observation(next(values)),
    )

    assert len(result.samples) == 3

    assert result.summary.successful_runs == 3
    assert result.summary.failed_runs == 0
    assert result.summary.invalid_runs == 0

    assert result.summary.total_time.mean == 400
    assert result.summary.total_time.count == 3


def test_warmup_excluded_from_statistics():
    values = iter(
        [
            1000,
            900,
            300,
            400,
            500,
        ]
    )

    result = run_benchmark(
        make_config(warmup_runs=2),
        experiment=lambda _: make_observation(next(values)),
    )

    assert len(result.samples) == 5

    assert result.samples[0].warmup
    assert result.samples[1].warmup
    assert not result.samples[2].warmup

    assert result.summary.total_time.count == 3
    assert result.summary.total_time.mean == 400


def test_field_run_is_preserved():
    outcomes = iter(
        [
            make_observation(300),
            LaunchError("ADB timeount"),
            make_observation(500),
        ]
    )

    def experiment(_):
        outcome = next(outcomes)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome

    result = run_benchmark(
        make_config(),
        experiment,
    )

    assert len(result.samples) == 3

    assert result.samples[1].status == RunStatus.FAILED
    assert result.samples[1].error == "ADB timeout"

    assert result.summary.successful_runs == 2
    assert result.summary.failed_runs == 1
    assert result.summary.total_time.mean == 400

    assert result.summary.success_rate == pytest.approx(2 / 3)


def test_invalid_scenario_is_preserved():

    def experiment(_):
        raise InvalidScenarioError("Process disappeared")

    result = run_benchmark(
        make_config(),
        experiment,
    )

    assert result.summary.invalid_runs == 3
    assert result.summary.successful_runs == 0
    assert result.summary.total_time.mean is None


def test_classification_mismatch_is_invalid():
    # Observation claims cold start but a process
    # already existed before the launch.
    from dataclasses import replace

    observation = replace(
        make_observation(),
        pid_before=1234,
    )

    result = run_benchmark(
        make_config(iterations=1),
        experiment=lambda _: observation,
    )

    assert result.samples[0].status == RunStatus.INVALID
    assert result.samples[0].status is not None

    assert result.summary.total_time.count == 0


def test_missing_timing_not_treated_as_zero():

    values = iter(
        [
            300,
            None,
            500,
        ]
    )

    result = run_benchmark(
        make_config(),
        experiment=lambda _: make_observation(next(values)),
    )

    assert result.summary.successful_runs == 3
    assert result.summary.total_time.count == 2
    assert result.summary.total_time.mean == 400
    assert result.summary.host_elapsed.count == 3


def test_warmup_failure_excluded_from_summary():
    outcomes = iter(
        [
            LaunchError("Warm-up failed"),
            make_observation(400),
        ]
    )

    def experiment(_):
        outcome = next(outcomes)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome

    result = run_benchmark(
        make_config(
            iterations=1,
            warmup_runs=1,
        ),
        experiment=experiment,
    )

    assert result.samples[0].status == RunStatus.FAILED

    assert result.summary.failed_runs == 0
    assert result.summary.successful_runs == 1


def test_programming_errors_are_not_swallowed():

    def experiment(_):
        raise TypeError("Programming bug")

    with pytest.raises(TypeError):
        run_benchmark(
            make_config(),
            experiment=experiment,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"iterations": 0},
        {"iterations": -1},
        {"warmup_runs": -1},
        {"interval_seconds": -1},
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        BenchmarkConfig(
            launch_type=LaunchType.COLD,
            **kwargs,
        )

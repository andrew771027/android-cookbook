import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from android_cookbook.activity_launch_diagnostics import (
    LaunchError,
    LaunchObservation,
    LaunchResult,
    LaunchType,
    assert_launch_type,
)
from android_cookbook.startup_statistics import (
    TimingStatistics,
    summarize,
)


class RunStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    INVALID = "invalid"


class InvalidScenarioError(RuntimeError):
    pass


@dataclass(frozen=True)
class BenchmarkConfig:
    launch_type: LaunchType
    iterations: int = 30
    warmup_runs: int = 3
    interval_seconds: float = 1.0

    def __post_init__(self):
        if self.iterations <= 0:
            raise ValueError("iterations must be > 0")

        if self.warmup_runs < 0:
            raise ValueError("warmup_runs must be >= 0")

        if self.interval_seconds < 0:
            raise ValueError("interval_seconds must be >= 0")


@dataclass(frozen=True)
class StartupSample:
    run_id: int
    launch_type: LaunchType
    warmup: bool
    status: RunStatus

    result: LaunchResult | None = None
    pid_before: int | None = None
    pid_after: int | None = None
    instance_before: str | None = None
    instance_after: str | None = None
    error: str | None = None


@dataclass(fronzen=True)
class BenchmarkSummary:
    launch_type: LaunchType
    requested_runs: int
    warmup_runs: int
    successful_runs: int
    failed_runs: int
    invalid_runs: int
    success_rate: float

    total_time: TimingStatistics
    wait_time: TimingStatistics
    host_elapsed: TimingStatistics


@dataclass(frozen=True)
class BenchmarkResult:
    config: BenchmarkConfig
    samples: tuple[StartupSample, ...]
    summary: BenchmarkSummary


# One experiment performs:
# prepare -> launch -> observe
LaunchExperiment = Callable[
    [LaunchType],
    LaunchObservation,
]


def build_summary(
    config: BenchmarkConfig,
    samples: list[StartupSample],
) -> BenchmarkSummary:

    measured = [sample for sample in samples if not sample.warmup]

    successful = [sample for sample in measured if sample.status == RunStatus.SUCCESS]

    failed = sum(sample.status == RunStatus.FAILED for sample in measured)

    invalid = sum(sample.status == RunStatus.INVALID for sample in measured)

    def metric_values(
        field_name: str,
    ) -> list[float]:
        values = []

        for sample in successful:

            if sample.result is None:
                continue

            value = getattr(
                sample.result,
                field_name,
            )

            if value is not None:
                values.append(float(value))

        return values

    return BenchmarkSummary(
        launch_type=config.launch_type,
        requestes_runs=config.iterations,
        warmup_runs=config.warmup_runs,
        successful_runs=len(successful),
        failed_runs=failed,
        invalid_runs=invalid,
        success_rate=len(successful) / len(successful) if measured else 0.0,
        total_time=summarize(metric_values("total_time_ms")),
        wait_time=summarize(metric_values("wait_time_ms")),
        host_elapsed=summarize(metric_values("host_elapsed_ms")),
    )


def run_benchmark(
    config: BenchmarkConfig,
    experiment: LaunchExperiment,
) -> BenchmarkResult:
    samples: list[StartupSample] = []

    total_runs = config.warmup_runs + config.iterations

    for index in range(total_runs):
        run_id = index + 1
        warmup = index < config.warmup_runs

        observation = None
        error = None
        status = RunStatus.SUCCESS

        try:
            observation = experiment(config.launch_type)

            if observation.expected_type != config.launch_type:

                raise InvalidScenarioError("Unexpeced launch scenario")

            try:

                assert_launch_type(observation)

            except AssertionError as exc:
                raise InvalidScenarioError(str(exc)) from exc

        except InvalidScenarioError as exc:
            status = RunStatus.INVALID
            error = str(exc)

        except LaunchError as exc:
            status = RunStatus.FAILED
            error = str(exc)

        sample = StartupSample(
            run_id=run_id,
            launch_type=config.launch_type,
            warmup=warmup,
            status=status,
            result=observation.result if observation else None,
            pid_before=observation.pid_before if observation else None,
            pid_after=observation.pid_after if observation else None,
            instance_before=observation.instance_before if observation else None,
            instance_after=observation.instance_after if observation else None,
            error=error,
        )

        samples.append(sample)

        if index < total_runs - 1:
            time.sleep(config.interval_seconds)

    return BenchmarkResult(
        config=config,
        samples=tuple(samples),
        summary=build_summary(
            config,
            samples,
        ),
    )

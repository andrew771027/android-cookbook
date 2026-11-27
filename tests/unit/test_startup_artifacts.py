import csv
import json

from android_cookbook.activity_launch_diagnostics import (
    LaunchObservation,
    LaunchResult,
    LaunchType,
)
from android_cookbook.startup_artifacts import (
    create_artifact_directory,
    write_artifacts,
)
from android_cookbook.startup_performance import (
    BenchmarkConfig,
    run_benchmark,
)


def make_result(total_time=400):
    observation = LaunchObservation(
        expected_type=LaunchType.COLD,
        pid_before=None,
        pid_after=1234,
        instance_before=None,
        instance_after="instance-a",
        created_after_launch=True,
        result=LaunchResult(
            status="ok",
            launch_state="COLD",
            activity="example/.MainActivity",
            this_time_ms=None,
            total_time_ms=total_time,
            wait_time_ms=450,
            host_elapsed_ms=500.0,
            warning=None,
            raw_output="Status: ok\nComplete",
        ),
    )

    return run_benchmark(
        BenchmarkConfig(
            launch_type=LaunchType.COLD,
            iterations=2,
            warmup_runs=1,
            interval_seconds=0,
        ),
        experiment=lambda _: observation,
    )


def test_artifact_files_created(tmp_path):

    result = make_result()

    write_artifacts(
        result,
        tmp_path,
        environment={"api_level": "36"},
    )

    assert (tmp_path / "samples.csv").is_file()
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "environment.json").is_file()

    raw_files = list((tmp_path / "raw").glob("*.txt"))

    assert len(raw_files) == 3


def test_csv_contains_all_samples(tmp_path):

    write_artifacts(
        make_result(),
        tmp_path,
        environment={},
    )

    with (tmp_path / "samples.csv").open(
        encoding="utf-8",
        newline="",
    ) as file:

        rows = list(csv.DictReader(file))

    assert len(rows) == 3

    assert rows[0]["warmup"] == "True"
    assert rows[1]["warmup"] == "False"
    assert rows[1]["total_time_ms"] == "400"


def test_json_summary(tmp_path):

    write_artifacts(
        make_result(),
        tmp_path,
        environment={},
    )

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))

    assert summary["schema_version"] == 1
    assert summary["timing_unit"] == "ms"

    statistics = summary["summary"]["total_time"]

    assert statistics["count"] == 2
    assert statistics["mean"] == 400


def test_missing_timing_serialization(tmp_path):

    write_artifacts(
        make_result(total_time=None),
        tmp_path,
        environment={},
    )

    with (tmp_path / "samples.csv").open(
        encoding="utf-8",
        newline="",
    ) as file:

        rows = list(csv.DictReader(file))

    assert rows[0]["total_time_ms"] == ""

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))

    assert summary["summary"]["total_time"]["mean"] is None


def test_raw_output_preserved(tmp_path):

    write_artifacts(
        make_result(),
        tmp_path,
        environment={},
    )

    output = (tmp_path / "raw" / "run_001.txt").read_text(encoding="utf-8")

    assert output == "Status: ok\nComplete"


def test_unique_artifact_directories(tmp_path):
    first = create_artifact_directory(
        tmp_path,
        "cold",
    )

    second = create_artifact_directory(
        tmp_path,
        "cold",
    )

    assert first != second
    assert first.is_dir()
    assert second.is_dir()

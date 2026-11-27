import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from android_cookbook.package_manager import (install_apk, package_exists,)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.destructive,
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def benchmark_app(
    android_serial,
    test_apk,
    clean_test_package,
):

    package_name = clean_test_package

    install_apk(
        android_serial,
        test_apk,
        allow_test_packages=True,
    )

    assert package_exists(
        serial=android_serial,
        package_name=package_name,
    )

    return package_name

@pytest.mark.parametrize(
    "launch_type",
    [
        "cold",
        "warm",
        "hot",
    ],
)
def test_startup_benchmark_pipeline(
    android_serial,
    benchmark_app,
    tmp_path,
    launch_type,
):
    output_directory = tmp_path / "startup"

    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "examples" / "startup_benchmark.py"),
            "--serial",
            android_serial,
            "--type",
            launch_type,
            "--iterations",
            "3",
            "--warmup",
            "1",
            "--interval",
            "0",
            "--output",
            str(output_directory),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    directories = list(output_directory.iterdir())

    assert len(directories) == 1

    artifact_dir = directories[0]

    assert (artifact_dir / "samples.csv").exists()
    assert (artifact_dir / "summary.json").exists()
    assert (artifact_dir / "environment.json").exists()

    summary = json.loads(
        (artifact_dir / "summary.json").read_text(encoding="utf-8")
    )["summary"]

    with (artifact_dir / "samples.csv").open(
        encoding="utf-8",
        newline="",
    ) as file:

        rows = list(csv.DictReader(file))

    # Three measured runs plus one warm-up
    assert len(rows) == 4

    assert summary["requested_runs"] == 3
    assert summary["warmup_runs"] == 1

    assert summary["successful_runs"] + summary["failed_runs"] + summary["invalid_runs"] == 3

    # Verify the experiment succeeded.
    assert completed.returncode == 0, (
        completed.stdout
        + "\n"
        + completed.stderr
        + "\n"
        + str(summary)
    )

    assert summary("successful_runs") == 3

    # Host elapsed must exist for every valid launch.
    assert summary["host_elapsed"]["count"] == 3
    assert summary["host_elapsed"]["minimum"] >= 0

    # TotalTime may be missing for some launch paths
    assert 0 <= summary["total_time"]["count"] <= 3
import csv
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from android_cookbook.startup_performance import (
    BenchmarkResult,
)
from android_cookbook.startup_statistics import (
    PERCENTILE_METHOD,
)


def collect_environment(
    serial: str,
) -> dict:

    def adb_value(*args: str) -> str | None:

        try:

            completed = subprocess.run(
                [
                    "adb",
                    "-s",
                    serial,
                    *args,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            return completed.stdout.strip()

        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return None

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python": sys.versoin,
        },
        "android": {
            "serial": serial,
            "api_level": adb_value(
                "shell",
                "getprop",
                "ro.build.version.sdk",
            ),
            "product": adb_value(
                "shell",
                "getprop",
                "ro.build.model",
            ),
            "abi": adb_value(
                "shell",
                "getprop",
                "ro.product.cpu.abi",
            ),
            "build_fingerprint": adb_value(
                "shell",
                "getprop",
                "ro.build.fingerprint",
            ),
        },
    }


def create_artifact_directory(
    root: Path,
    launch_type: str,
) -> Path:

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    run_id = uuid4().hex[:8]

    directory = root / (f"{timestamp}-{launch_type}-{run_id}")

    directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    return directory


def write_json(
    path: Path,
    data: dict,
) -> None:
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_artifacts(
    result: BenchmarkResult,
    directory: Path,
    environment: dict,
) -> None:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_directory = directory / "raw"
    raw_directory.mkdir(exist_ok=True)

    fieldnames = [
        "run_id",
        "launch_type",
        "warmup",
        "status",
        "reported_launch_state",
        "pid_before",
        "pid_after",
        "instance_before",
        "instance_after",
        "this_time_ms",
        "total_time_ms",
        "wait_time_ms",
        "host_elapsed_ms",
        "error",
    ]

    with (directory / "sample.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for sample in result.samples:
            launch = sample.result

            writer.writerow(
                {
                    "run_id": sample.run_id,
                    "launch_type": sample.launch_type.value,
                    "warmup": sample.status.value,
                    "reported_launch_state": launch.launch_state if launch else None,
                    "pid_before": sample.pid_before,
                    "pid_after": sample.pid_after,
                    "instance_before": sample.instance_before,
                    "instance_after": sample.instance_after,
                    "this_time_ms": launch.this_time_ms if launch else None,
                    "wait_time_ms": launch.wait_time_ms if launch else None,
                    "host_elapsed_ms": launch.host_elapsed_ms if launch else None,
                    "error": sample.error,
                }
            )

            raw_path = raw_directory / (f"run_{sample.run_id:03d}.txt")

            sections = []

            if launch:
                sections.append(launch.raw_output)

            if sample.error:
                sections.append(f"Error: {sample.error}")

            raw_path.write_text(
                "\n".join(sections),
                encoding="utf-8",
            )

    write_json(
        directory / "summary.json",
        {
            "schema_version": 1,
            "timing_unit": "ms",
            "percentile_method": PERCENTILE_METHOD,
            "stddev_method": "sample",
            "config": asdict(result.config),
            "summary": asdict(result.summary),
        },
    )

    write_json(
        directory / "environment.json",
        environment,
    )

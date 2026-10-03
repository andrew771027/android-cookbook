# Android Cookbook

Learn to inspect Android devices with Android Debug Bridge (ADB) and Python. This project
covers device discovery, shell commands, system properties, and package management. Tests
include unit tests and checks that run on an emulator or physical device.

## Before you begin

Install Python 3.14 or later, Poetry 2.x, and Android SDK Platform Tools. To run device
commands, connect an emulator or enable USB debugging on a physical device.
See [Set up your environment](docs/environment.md) for instructions.

The shell examples use Bash or Zsh. Run project commands from the repository root.

## Get started

Install dependencies and run the unit tests:

```bash
poetry install
PYTHONPATH=src poetry run pytest tests/unit
```

Check that your device appears with the state `device`:

```bash
adb devices -l
```

Print its model, Android version, SDK level, and build properties as JSON:

```bash
PYTHONPATH=src poetry run python -m android_cookbook.device_info
# Equivalent Makefile target
make exec_device_info
```

This target sets `PYTHONPATH=src` and runs `android_cookbook.device_info` with Poetry's
`python3`. Install dependencies with `poetry install` and connect an online device first.

The command selects the first online device. For the output fields and examples, see
[Read Android properties](docs/receipes/v0.3-properties.md).

To inspect the shell user, kernel, and root directory, run:

```bash
PYTHONPATH=src poetry run python -m android_cookbook.shell_info
```

**Known issue:** The shell command's `cwd` field currently repeats the kernel information.
See [Shell output](docs/receipes/v0.2-adb-shell.md#5-print-shell-information) for details.

Inspect an installed package and its APK paths as JSON:

```bash
PYTHONPATH=src poetry run python -m android_cookbook.package_info --package com.android.settings
# Equivalent Makefile target
make exec_package_info
```

The command requires `--package` and selects the first online device. See
[Package manager](docs/receipes/v0.4-package-manager.md) for example output and app management helpers.

## Run tests

```bash
# Unit tests: no device required
PYTHONPATH=src poetry run pytest tests/unit

# Integration tests: requires ADB and an online device
PYTHONPATH=src poetry run pytest tests/integration

# All tests
PYTHONPATH=src poetry run pytest
```

Package lifecycle integration tests install, clear, and uninstall the disposable fixture
app when enabled. The checked-in APK is empty, and all five tests currently have unconditional
`skip` markers, so their fixtures and device operations do not run. See
[v0.4.1: Package lifecycle](docs/receipes/v0.4.1-package-lifecycle.md) before running them.
The lifecycle state machine unit test runs against an in-memory fake with a `100 × 30`
example/step budget. Its device counterpart uses `3 × 5` and conditionally skips while
the APK is missing or empty. See the recipe for model rules and enablement instructions.
To run integration checks without tests marked destructive:

```bash
PYTHONPATH=src poetry run pytest tests/integration -m "integration and not destructive"
```

Integration tests use the first online device and skip if none is connected. If ADB is
missing or a command fails, the tests report an error.

## Find your way around

| Path | Contents |
| --- | --- |
| `src/android_cookbook/adb.py` | ADB execution and device discovery |
| `src/android_cookbook/shell.py` | Shell commands and output handling |
| `src/android_cookbook/package_manager.py` | Package queries, APK paths, and app management |
| `src/android_cookbook/package_lifecycle.py` | Install, inspect, clear, uninstall, and collect lifecycle results |
| `src/android_cookbook/package_info.py` | Package installation status and APK paths as JSON |
| `src/android_cookbook/properties.py` | Property reads, parsing, and collection |
| `src/android_cookbook/device_info.py` | Device properties as JSON |
| `src/android_cookbook/shell_info.py` | Shell information as JSON |
| `tests/unit/` | Tests using sample responses and an in-memory lifecycle state machine |
| `tests/integration/` | Tests that run commands on a device |
| `tests/fixtures/test_app/` | Disposable app requirements and an empty APK placeholder |
| `scripts/health_check.sh` | ADB and emulator environment check |

## Learn more

- [Set up your environment](docs/environment.md)
- [Understand the architecture](docs/architecture.md)
- [v0.1: Run ADB from Python](docs/receipes/v0.1-adb-basics.md)
- [v0.2: Inspect the Android shell](docs/receipes/v0.2-adb-shell.md)
- [v0.3: Read Android properties](docs/receipes/v0.3-properties.md)
- [v0.4: Inspect and manage packages](docs/receipes/v0.4-package-manager.md)
- [v0.4.1: Test the package lifecycle](docs/receipes/v0.4.1-package-lifecycle.md)
- [Roadmap](Roadmap.md)
- [Commit checklist](CommitManual.md)

## Limitations

The JSON commands always use the first online device and have no device-selection option.
ADB calls have no timeout. Property collection requires an SDK value that Python can convert
to an integer. See [Architecture](docs/architecture.md) for error handling and parser behavior.

# Android Cookbook

Learn to inspect Android devices with Android Debug Bridge (ADB) and Python. This project
covers device discovery, shell commands, system properties, package management,
Activity Manager operations, Activity lifecycle observation, and rotation-driven Activity
recreation, background process death, saved state recovery, and cold, warm, and hot
launch diagnostics (v0.5.4). Tests include
unit tests and checks that run on an emulator or physical device.

## Before you begin

Install Python 3.14 or later, Poetry 2.x, and Android SDK Platform Tools. To run device
commands, connect an emulator or enable USB debugging on a physical device.
See [Set up your environment](docs/environment.md) for instructions.

To build the test APK, use JDK 17 and Gradle 9.3.1 together with the Android
Environment SDK and build tools: Android SDK Platform 36 and Build Tools 36.0.0.
Platform Tools provides ADB; APK compilation also needs the SDK platform and Build Tools.
Follow [Build the test APK](docs/receipes/v0.4.2-test-apk-fixture.md#build-the-test-apk)
for Gradle installation, the macOS Homebrew workaround, SDK setup, and build commands.

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

# Integration tests: excludes destructive tests by default
PYTHONPATH=src poetry run pytest tests/integration

# Default suite: excludes destructive tests
PYTHONPATH=src poetry run pytest
```

Build the disposable APK before running package lifecycle, Activity Manager, Activity
lifecycle, Activity recreation, process recovery, or launch diagnostics integration tests:

```bash
./scripts/build-test-apk.sh
```

The fixed-sequence package lifecycle, Activity Manager, Activity lifecycle, Activity
recreation, process recovery, and launch diagnostics tests use the dedicated emulator selected by
`ANDROID_SERIAL`. Opt in to these destructive tests explicitly:

```bash
export ANDROID_SERIAL=emulator-5554
PYTHONPATH=src poetry run pytest tests/integration/test_activity_manager.py \
  tests/integration/test_package_lifecycle.py \
  tests/integration/test_activity_lifecycle.py \
  tests/integration/test_activity_recreation.py \
  tests/integration/test_process_recovery.py \
  tests/integration/test_activity_launch_diagnostics.py -m "integration and destructive" -v
```

The tests require the fixture package to be absent before setup, then install and remove it.
Activity tests launch `.MainActivity`, inspect its process, force-stop, restart, and read
diagnostics. Activity lifecycle tests observe launch, Home, return from Home, and graceful
finish through Logcat. They clear the shared Logcat buffer, so run them sequentially on
a dedicated emulator. Rebuild the APK after changing the fixture source. The state machine
also enables and disables the package. Use an Android Environment
emulator running API 31 or later. See [Build the test APK](docs/receipes/v0.4.2-test-apk-fixture.md)
for setup and [Package lifecycle](docs/receipes/v0.4.1-package-lifecycle.md) for test behavior.
The state machine uses a `100 × 30` example/step budget in unit tests and `3 × 5`
on a device. Device tests skip when the required APK or an online device is unavailable;
the state machine also rejects an empty APK before connecting to the device.

To run integration checks without tests marked destructive:

```bash
PYTHONPATH=src poetry run pytest tests/integration -m "integration and not destructive"
```

Read-only integration tests and the lifecycle state machine use the first online device.
Tests using the shared fixtures require `ANDROID_SERIAL` to name an online `emulator-*`
device and skip if that selection is missing or unavailable. `pytest.ini` excludes
`destructive` tests by default; an explicit `-m integration` includes them. If ADB is
missing or a command fails, the tests report an error.

### Before committing

The commands above support day-to-day development. Before every commit, follow the
[commit checklist](CommitManual.md#run-the-full-integration-suite): rebuild the APK,
leave only the dedicated test emulator online, and remove any existing fixture
installation. Keep the emulator unlocked and run tests sequentially.

```bash
./scripts/build-test-apk.sh
export ANDROID_SERIAL=emulator-5554
adb devices -l
adb -s "$ANDROID_SERIAL" get-state
# If the fixture is installed, uninstall it before testing.
adb -s "$ANDROID_SERIAL" shell pm list packages com.example.androidcookbook.fixture
make test
git diff --check
```

Both suites must pass completely, with no failures, errors, skipped tests, or deselected
tests. Resolve missing prerequisites and rerun if any tests skip. Confirm the fixture
package is absent after teardown.

Activity recreation tests also change system rotation settings, restore their captured
values during teardown, and verify counter restoration in a new Activity instance. See
[Activity recreation](docs/receipes/v0.5.2-activity-recreation.md).

Process recovery tests background the app, request `am kill`, confirm process absence,
and relaunch the saved task to validate its PID, instance UUID, and restored counter.
See [Process death and state recovery](docs/receipes/v0.5.3-process-death-recovery.md).

Launch diagnostics compare process PID, Activity UUID, and callbacks across cold, warm,
and hot launches. Timing fields remain optional. Warm and hot tests can skip when the
process does not survive setup; these skips do not satisfy the commit checklist. See
[Activity launch diagnostics](docs/receipes/v0.5.4-activity-launch-diagnostics.md), including
polling behavior, test coverage, and diagnostic limitations.

The Makefile exports `ANDROID_SERIAL`, defaulting to `emulator-5554`. Override it with
`make <target> ANDROID_SERIAL=emulator-5556` when using another dedicated emulator.

| Target | Behavior |
| --- | --- |
| `make build_apk` | Build and copy the fixture APK |
| `make init_android_serial` | Print the selected serial |
| `make cleanup_apk` | Uninstall the fixture if present; leave an absent package alone |
| `make test_unit` | Run all unit tests |
| `make test_integration` | Run only tests marked both `integration` and `destructive` |
| `make test_all_integration` | Run the complete integration suite, including destructive tests |
| `make test` | Run all unit and integration tests, including destructive tests |

`make test` clears the default marker filter in `pytest.ini` with `-m ""` and reports skip reasons.
Build the fixture APK and prepare a dedicated emulator before running it.

## Find your way around

| Path | Contents |
| --- | --- |
| `src/android_cookbook/activity_launch_diagnostics.py` | Launch timing parsing, PID lookup, controlled launch assertions, and Displayed event parsing |
| `src/android_cookbook/adb.py` | ADB execution and device discovery |
| `src/android_cookbook/shell.py` | Shell commands and output handling |
| `src/android_cookbook/process_recovery.py` | PID-aware state parsing, process polling, launcher task recovery, and recovery assertions |
| `src/android_cookbook/activity_recreation.py` | State log parsing, state polling, rotation capture and restoration, and fixture actions |
| `src/android_cookbook/activity_lifecycle.py` | Lifecycle log parsing, ordered event polling, Home/Back key events, and graceful finish |
| `src/android_cookbook/activity_manager.py` | Activity launch, force-stop, exact process lookup, and activity diagnostics |
| `src/android_cookbook/package_manager.py` | Package queries, APK paths, and app management |
| `src/android_cookbook/package_lifecycle.py` | Install, inspect, clear, uninstall, and collect lifecycle results |
| `src/android_cookbook/package_info.py` | Package installation status and APK paths as JSON |
| `src/android_cookbook/properties.py` | Property reads, parsing, and collection |
| `src/android_cookbook/device_info.py` | Device properties as JSON |
| `src/android_cookbook/shell_info.py` | Shell information as JSON |
| `tests/unit/` | Tests using sample responses and an in-memory lifecycle state machine |
| `tests/integration/` | Tests that run commands on a device |
| `tests/fixtures/test-app/` | Generated test APK and fixture requirements |
| `fixtures/test-app/` | Android source and Gradle Wrapper scripts for the test APK |
| `scripts/build-test-apk.sh` | Build the fixture and copy its APK to the integration test path |
| `scripts/health_check.sh` | ADB and emulator environment check |

## Learn more

- [Set up your environment](docs/environment.md)
- [Understand the architecture](docs/architecture.md)
- [v0.1: Run ADB from Python](docs/receipes/v0.1-adb-basics.md)
- [v0.2: Inspect the Android shell](docs/receipes/v0.2-adb-shell.md)
- [v0.3: Read Android properties](docs/receipes/v0.3-properties.md)
- [v0.4: Inspect and manage packages](docs/receipes/v0.4-package-manager.md)
- [v0.4.1: Test the package lifecycle](docs/receipes/v0.4.1-package-lifecycle.md)
- [v0.4.2: Build the test APK](docs/receipes/v0.4.2-test-apk-fixture.md)
- [v0.5.0: Start activities and inspect processes](docs/receipes/v0.5.0-activity-manager.md)
- [v0.5.1: Observe Activity lifecycle callbacks](docs/receipes/v0.5.1-activity-lifecycle.md)
- [v0.5.2: Recreate an Activity and restore state](docs/receipes/v0.5.2-activity-recreation.md)
- [v0.5.3: Recover state after process death](docs/receipes/v0.5.3-process-death-recovery.md)
- [v0.5.4: Diagnose cold, warm, and hot launches](docs/receipes/v0.5.4-activity-launch-diagnostics.md)
- [Roadmap](Roadmap.md)
- [Commit checklist](CommitManual.md)

## Limitations

The JSON commands always use the first online device and have no device-selection option.
Activity lifecycle ADB calls have a 20-second timeout. Launch diagnostics use a
30-second launch timeout and a 10-second PID lookup timeout; other ADB wrappers have no timeout.
Property collection requires an SDK value that Python can convert to an integer. See [Architecture](docs/architecture.md) for error handling and parser behavior.

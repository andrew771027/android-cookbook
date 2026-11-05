# Set up your environment

Install the Python dependencies and Android tools, connect a device, then run the project.
The command examples use Bash or Zsh; run project commands from the repository root.

## Requirements

| Tool | Required | Purpose |
| --- | --- | --- |
| Git | Yes | Source control |
| Python 3.14+ | Yes | Version declared by `pyproject.toml` |
| Poetry 2.x | Yes | Dependencies and virtual environments |
| Android SDK Platform Tools | Yes | Provides `adb` and `fastboot` |
| Android Emulator or physical device | For device commands | Runs integration tests and supplies live output |

Poetry installs `pytest`, `hypothesis`, and `pre-commit` from the project dependencies.

## 1. Install Android Platform Tools

Install Android Studio or standalone Platform Tools, then add the directory containing `adb` to
`PATH`. Typical SDK roots are `$HOME/Library/Android/sdk` on macOS, `$HOME/Android/Sdk` on Linux,
and `%LOCALAPPDATA%\Android\Sdk` on Windows.

For macOS with the default location:

```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$PATH:$ANDROID_HOME/platform-tools"
export PATH="$PATH:$ANDROID_HOME/emulator"
```

## 2. Verify Android tools

```bash
adb version
adb start-server
adb devices -l
bash scripts/health_check.sh
```

The health check verifies ADB, starts its server, lists devices, and reports the emulator version
when that command is available.

## 3. Prepare a device

Start an Android Virtual Device, or enable Developer options and USB debugging on a physical
device. For hardware, unlock it and accept the RSA authorization prompt.

Look for `device` in the second column:

```text
List of devices attached
emulator-5554 device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64
```

- `unauthorized`: unlock the device and approve USB debugging.
- `offline`: reconnect it or restart ADB.
- No rows: check the cable, USB mode, SDK path, or emulator status.

If the device is offline, restart ADB. This disconnects existing ADB sessions:

```bash
adb kill-server
adb start-server
adb devices -l
```

## 4. Install and run the project

```bash
poetry install
poetry run python --version
poetry run pytest --version
```

The Python package lives under `src/`. Set `PYTHONPATH=src` so the commands can find it,
including when the package has not been installed into the active environment:

```bash
# Android build properties
PYTHONPATH=src poetry run python -m android_cookbook.device_info

# Package installation status and APK paths
PYTHONPATH=src poetry run python -m android_cookbook.package_info --package com.android.settings

# Shell user, directory, kernel, and root entries
PYTHONPATH=src poetry run python -m android_cookbook.shell_info
```

All three commands select the first online device. For output examples and known issues, see
[Android properties](receipes/v0.3-properties.md#4-print-json),
[ADB shell](receipes/v0.2-adb-shell.md#5-print-shell-information), and
[Package manager](receipes/v0.4-package-manager.md#3-print-a-package-report).

Package inspection requires no extra dependencies. To try installation, supply a local test
APK; use a disposable test app for uninstalling, clearing data, or changing enabled state.
`make exec_package_info` runs the package report for `com.android.settings`.

## 5. Run tests

Unit tests use sample responses in place of ADB calls. They do not require a device:

```bash
PYTHONPATH=src poetry run pytest tests/unit
PYTHONPATH=src poetry run pytest tests/unit/test_shell.py -v
```

Integration tests invoke local ADB and need an online device:

```bash
PYTHONPATH=src poetry run pytest tests/integration -m "integration and not destructive"
PYTHONPATH=src poetry run pytest tests/integration/test_shell.py -m integration -v
```

Package lifecycle integration tests also require a valid APK with package name
`com.example.androidcookbook.fixture` at `tests/fixtures/test-app/cookbook-test-app.apk`.
Build it with `./scripts/build-test-apk.sh` before running the device tests. Building
requires JDK 17, Gradle 9.3.1, Android SDK Platform 36, and Build Tools 36.0.0 from
Android Environment. Platform Tools alone does not provide the APK build tools.
Follow [Build the test APK](receipes/v0.4.2-test-apk-fixture.md#build-the-test-apk)
for installation and SDK configuration, including the macOS Homebrew workaround.
Use an emulator or device running API 31 or later.

The fixed-sequence package lifecycle, APK installation, Activity Manager, Activity
lifecycle, recreation, and process recovery tests require an online dedicated emulator
selected with `ANDROID_SERIAL`:

```bash
export ANDROID_SERIAL=emulator-5554
PYTHONPATH=src poetry run pytest tests/integration/test_activity_manager.py \
  tests/integration/test_package_lifecycle.py \
  tests/integration/test_activity_lifecycle.py \
  tests/integration/test_activity_recreation.py \
  tests/integration/test_process_recovery.py -m "integration and destructive" -v
```

Shared fixtures skip for an unset, non-emulator, or unavailable serial. They fail if the
fixture package is already installed. Remove a leftover manual installation before running:

```bash
adb -s "$ANDROID_SERIAL" uninstall com.example.androidcookbook.fixture
```

Activity tests require the current v0.5.3 fixture APK. Its lifecycle marker remains
`android-cookbook-v0.5.1`; state logs retain `android-cookbook-v0.5.2` and now include `pid`.
After changing the Java source,
run `./scripts/build-test-apk.sh` to refresh the APK that pytest installs; `installDebug`
alone does not update that artifact. Run lifecycle tests sequentially, with the emulator
unlocked and no other automation changing the foreground Activity or clearing Logcat.
These tests clear the shared Logcat buffer during setup. See the
[Activity lifecycle recipe](receipes/v0.5.1-activity-lifecycle.md) for log format and timeout diagnostics.

Activity recreation tests also need an emulator where rotation 0 produces portrait and
rotation 1 produces landscape. They capture both system rotation settings and attempt
to restore them during teardown. After launch, tests lock the running Activity to portrait
with `wm user-rotation lock 0` and wait for its portrait event before modifying state.
Setting rotation before launch alone did not reliably establish that baseline. See
[rotation root cause and solution](receipes/v0.5.2-activity-recreation.md#v053-rotation-fix-root-cause-and-solution).

Process recovery tests require state logs ending in `pid=<number>`. A stale APK without
that field produces events the process parser cannot accept. Rebuild the APK rather than
increasing the wait timeout. Tests skip if `am kill` does not terminate the background
process within 10 seconds; such a skip does not satisfy the commit checklist. See
[Process death and state recovery](receipes/v0.5.3-process-death-recovery.md).

Teardown attempts force-stop and uninstallation, reporting cleanup failures. See the
[lifecycle recipe](receipes/v0.4.1-package-lifecycle.md) for commands and cleanup behavior.

The state machine unit test uses Hypothesis with an in-memory fake (`100` examples,
up to `30` steps) and needs no APK or device. Hypothesis is installed by `poetry install`.
The integration state machine uses `3` examples with up to `5` steps and conditionally
skips if the APK is missing or empty, before checking for an online device. Supply a
valid APK and device to enable it; no skip decorator needs to be removed for that test.
See the [state machine recipe](receipes/v0.4.1-package-lifecycle.md#6-test-the-package-lifecycle-as-a-state-machine)
for commands and cleanup behavior.

To exclude tests marked destructive:

```bash
PYTHONPATH=src poetry run pytest tests/integration -m "integration and not destructive"
```

The `integration` and `destructive` markers are registered in `pytest.ini`. Device checks skip when no device has
state `device`. Missing ADB or failed commands cause errors.
`PYTHONPATH=src poetry run pytest` and `make test` exclude destructive tests by default
through `pytest.ini`. An explicit `-m integration` (also used by `make test_all_integration`)
overrides that filter and includes destructive tests. Activity Manager needs no additional
Python dependencies; see the [v0.5.0 recipe](receipes/v0.5.0-activity-manager.md).

## 6. Verify before committing

Before every commit, rebuild the APK and run the complete unit and integration suites.
Leave only the dedicated test emulator online: some integration tests select the first
online device rather than `ANDROID_SERIAL`. Keep it unlocked, remove any existing
fixture installation as described above, and run sequentially without other automation.

```bash
./scripts/build-test-apk.sh
export ANDROID_SERIAL=emulator-5554
adb devices -l
adb -s "$ANDROID_SERIAL" get-state
PYTHONPATH=src poetry run pytest tests/unit
PYTHONPATH=src poetry run pytest tests/integration -m integration -v -rs
git diff --check
```

Require all tests to pass with no failures, errors, skips, or deselected tests. A missing
APK or device that causes skips must be fixed before committing. The default suite,
read-only runs, and file-specific runs are useful during development but do not replace
this full verification. Confirm cleanup removes the fixture package. See the
[commit checklist](../CommitManual.md#run-the-full-integration-suite) for the complete procedure.

## Optional development checks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

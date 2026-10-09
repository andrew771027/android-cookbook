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
PYTHONPATH=src poetry run pytest tests/integration -m integration
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

The five fixed-sequence tests run when the APK and an online device are available.
Their fixtures uninstall the disposable package before and after each test. See the
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
Run all tests with `PYTHONPATH=src poetry run pytest` or `make test`.

## Optional development checks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

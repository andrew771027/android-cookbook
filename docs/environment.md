# Android Cookbook Environment

This guide prepares a workstation to run the package, tests, and ADB commands against an emulator
or physical Android device.

## Requirements

| Tool | Required | Purpose |
| --- | --- | --- |
| Git | Yes | Source control |
| Python 3.14+ | Yes | Version declared by `pyproject.toml` |
| Poetry 2.x | Yes | Dependencies and virtual environments |
| Android SDK Platform Tools | Yes | Provides `adb` and `fastboot` |
| Android Emulator | Recommended | Repeatable integration-test device |
| Physical Android device | Optional | Real-hardware verification |

Poetry installs `pytest` and `pre-commit` from the project dependencies.

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

The expected second-column state is `device`:

```text
List of devices attached
emulator-5554 device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64
```

- `unauthorized`: unlock the device and approve USB debugging.
- `offline`: reconnect it or restart ADB.
- No rows: check the cable, USB mode, SDK path, or emulator status.

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

The project uses a `src/` layout, so expose it when running modules directly:

```bash
# Android build properties
PYTHONPATH=src poetry run python -m android_cookbook.device_info

# Shell user, directory, kernel, and root entries
PYTHONPATH=src poetry run python -m android_cookbook.shell_info
```

Both select the first online device. The current `shell_info` implementation has a known defect:
`cwd` duplicates kernel output even though `get_working_directory()` is available.

## 5. Run tests

Unit tests mock external boundaries and require no Android hardware:

```bash
poetry run pytest tests/unit
poetry run pytest tests/unit/test_shell.py -v
```

Integration tests invoke local ADB and need an online device:

```bash
poetry run pytest tests/integration -m integration
poetry run pytest tests/integration/test_shell.py -m integration -v
```

The `integration` marker is registered in `pytest.ini`. Device checks skip when no device has
state `device`. Run everything with `poetry run pytest` or `make test`.

## Optional development checks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

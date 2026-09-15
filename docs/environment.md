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

# Shell user, directory, kernel, and root entries
PYTHONPATH=src poetry run python -m android_cookbook.shell_info
```

Both commands select the first online device. For output examples and known issues, see
[Android properties](receipes/v0.3-properties.md#4-print-json) and
[ADB shell](receipes/v0.2-adb-shell.md#5-print-shell-information).

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

The `integration` marker is registered in `pytest.ini`. Device checks skip when no device has
state `device`. Missing ADB or failed commands cause errors.
Run all tests with `PYTHONPATH=src poetry run pytest` or `make test`.

## Optional development checks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

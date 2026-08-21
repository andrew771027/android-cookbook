# Android Cookbook Environment

This guide prepares a workstation to run the Python package, its tests, and ADB commands against
an emulator or physical Android device.

## Requirements

| Tool | Required | Purpose |
| --- | --- | --- |
| Git | Yes | Source control |
| Python 3.14+ | Yes | Version declared by `pyproject.toml` |
| Poetry 2.x | Yes | Dependency and virtual-environment management |
| Android SDK Platform Tools | Yes | Provides `adb` and `fastboot` |
| Android Emulator | Recommended | Provides a repeatable test device |
| Physical Android device | Optional | Tests behavior on real hardware |

`pytest` and `pre-commit` are installed from the project dependencies by Poetry.

## 1. Install Android Platform Tools

Install Android Studio or the standalone Android SDK Platform Tools, then make sure the directory
containing `adb` is present in `PATH`.

Typical SDK locations are:

- macOS: `$HOME/Library/Android/sdk`
- Linux: `$HOME/Android/Sdk`
- Windows: `%LOCALAPPDATA%\Android\Sdk`

For macOS or Linux, a shell configuration commonly includes:

```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$PATH:$ANDROID_HOME/platform-tools"
export PATH="$PATH:$ANDROID_HOME/emulator"
```

Adjust `ANDROID_HOME` for the SDK location on your machine, then open a new terminal.

## 2. Verify Android tools

```bash
adb version
adb start-server
adb devices -l
```

The repository also provides a health check:

```bash
bash scripts/health_check.sh
```

It verifies `adb`, starts the ADB server, lists devices, and reports the emulator version when the
`emulator` command is available.

## 3. Prepare a device

### Emulator

Create and start an Android Virtual Device (AVD) from Android Studio's Device Manager. Wait for
Android to finish booting, then run `adb devices -l`.

### Physical device

1. Enable Developer options.
2. Enable USB debugging.
3. Connect the device over USB.
4. Unlock the device and accept the computer's RSA authorization prompt.
5. Run `adb devices -l`.

The expected state is `device`:

```text
List of devices attached
emulator-5554 device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64
```

Common non-ready states:

- `unauthorized`: unlock the device and approve USB debugging.
- `offline`: reconnect the device or restart the ADB server.
- no rows: check the cable, USB mode, SDK path, or emulator status.

To restart ADB:

```bash
adb kill-server
adb start-server
adb devices -l
```

## 4. Install the Python project

From the repository root:

```bash
poetry install
```

Confirm the interpreter and test runner:

```bash
poetry run python --version
poetry run pytest --version
```

The project uses a `src/` layout. When running the module directly, expose that directory through
`PYTHONPATH`:

```bash
PYTHONPATH=src poetry run python -m android_cookbook.device_info
```

## 5. Run tests

Unit tests mock `subprocess.run` and do not require Android hardware:

```bash
poetry run pytest tests/unit
```

Integration tests invoke the local `adb` executable and need at least one online device for all
checks to execute:

```bash
poetry run pytest tests/integration -m integration
```

The current unit tests expect dictionaries while the implementation returns `AdbDevice`
instances. A mocked property test and one integration state check also contain typos, so the full
suite is expected to fail until the test contract is corrected.

## Optional development checks

Install Git hooks:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

The configured hooks check whitespace, common file formats, Python syntax, imports, formatting,
and Flake8 rules.

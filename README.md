# Android Cookbook

Android Cookbook is a small Python learning project for automating common Android Debug Bridge
(ADB) tasks. It discovers connected devices, reads Android system properties, and runs basic
shell-inspection commands on a selected device.

## Features

- Runs ADB commands through Python's `subprocess` module.
- Parses `adb devices` into immutable `AdbDevice` values.
- Reads properties from a specific device with `adb shell getprop`.
- Runs tokenized device commands through a reusable `run_shell()` wrapper.
- Reads the current user, working directory, kernel information, and root-directory entries.
- Prints device or shell information as JSON using the first online device.
- Separates mocked unit tests from tests that require a real device or emulator.

## Project layout

```text
android-cookbook/
├── src/android_cookbook/
│   ├── adb.py                 # ADB process wrapper and device parsing
│   ├── device_info.py         # Device-property JSON workflow
│   ├── shell.py               # Device shell wrapper and inspection helpers
│   └── shell_info.py          # Shell-information JSON workflow
├── tests/
│   ├── unit/                  # Tests with process boundaries mocked
│   └── integration/           # Tests against ADB and an online device
├── scripts/
├── docs/
│   ├── environment.md
│   ├── architecture.md
│   └── receipes/
│       ├── v0.1-adb-basics.md
│       └── v0.2-adb-shell.md
├── Makefile
├── pytest.ini
└── pyproject.toml
```

## Requirements

- Python 3.14 or newer
- Poetry 2.x
- Android SDK Platform Tools (`adb`)
- An emulator or physical Android device for integration tests and live output

See [Environment setup](docs/environment.md) for installation and device preparation.

## Quick start

```bash
poetry install
poetry run pytest tests/unit
PYTHONPATH=src poetry run python -m android_cookbook.device_info
PYTHONPATH=src poetry run python -m android_cookbook.shell_info
```

Before running commands against a device, confirm that it appears with state `device`:

```bash
adb devices -l
```

For a broader workstation check, run `bash scripts/health_check.sh`.

## Tests

```bash
# No Android device required
poetry run pytest tests/unit

# Requires adb and an online device; checks skip when none is available
poetry run pytest tests/integration -m integration

# Entire suite
poetry run pytest
```

Unit tests cover device parsing, property and shell command construction, and shell-output
transformations. Integration tests use the first device whose ADB state is `device`.

## Documentation

- [Environment setup](docs/environment.md)
- [Architecture](docs/architecture.md)
- [v0.1 ADB basics recipe](docs/receipes/v0.1-adb-basics.md)
- [v0.2 ADB shell recipe](docs/receipes/v0.2-adb-shell.md)

## Current constraints

- Both JSON workflows select the first online device; there is no CLI device selector.
- Commands have no explicit timeout or domain-specific error translation.
- `ProcessInfo` is defined for future process parsing but is not used yet.
- `shell_info.py` currently populates `cwd` with `get_kernel_info()` instead of
  `get_working_directory()`. The helper is implemented and unit-tested, but the JSON output
  duplicates the kernel value until that wiring is corrected.

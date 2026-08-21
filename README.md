# Android Cookbook

Android Cookbook is a small Python learning project for automating common Android Debug Bridge
(ADB) tasks. Version `0.1.0` focuses on discovering connected devices and reading basic Android
system properties.

## What it does

- Runs ADB commands through Python's `subprocess` module.
- Parses `adb devices` into `AdbDevice` values.
- Reads properties from a specific device with `adb shell getprop`.
- Selects the first online device and prints its information as JSON.
- Separates mocked unit tests from tests that require a real device or emulator.

Example output:

```json
{
  "serial": "emulator-5554",
  "model": "sdk_gphone64_arm64",
  "android_version": "16",
  "sdk": "36",
  "build": "BP2A.250705.008"
}
```

The actual values depend on the connected Android device.

## Project layout

```text
android-cookbook/
├── src/android_cookbook/
│   ├── adb.py                 # ADB process wrapper and device parsing
│   └── device_info.py         # Device-property collection and JSON output
├── tests/
│   ├── unit/test_adb.py       # Tests with subprocess mocked
│   └── integration/test_device.py
├── scripts/
│   ├── health_check.sh        # Checks local Android tooling and devices
│   └── virtual_environment.sh
├── docs/
│   ├── environment.md
│   ├── architecture.md
│   └── receipes/v0.1-adb-basics.md
│── Makefile                  # Run exec & test
└── pyproject.toml
```

## Requirements

- Python 3.14 or newer
- Poetry 2.x
- Android SDK Platform Tools (`adb`)
- An Android emulator or a physical Android device for integration tests and live output

See [Environment setup](docs/environment.md) for installation and device preparation.

## Quick start

```bash
poetry install
poetry run adb version
poetry run pytest tests/unit
PYTHONPATH=src poetry run python -m android_cookbook.device_info
```

Before running commands against a device, confirm that it appears with state `device`:

```bash
adb devices -l
```

For a broader workstation check:

```bash
bash scripts/health_check.sh
```

## Tests

Run mocked tests without a connected Android device:

```bash
poetry run pytest tests/unit
```

Run integration tests with an unlocked emulator or physical device connected:

```bash
poetry run pytest tests/integration -m integration
```

Run everything:

```bash
poetry run pytest
```

> Current development note: the checked-in tests and implementation are not fully aligned yet.
> `AdbDevice` exposes `serial` and `state`, while the unit tests still expect dictionaries with a
> `name` key. The mocked property test and one integration state check also contain typos. Those
> tests must be corrected before the complete suite will pass.

## Documentation

- [Environment setup](docs/environment.md)
- [Architecture](docs/architecture.md)
- [v0.1 ADB basics recipe](docs/receipes/v0.1-adb-basics.md)

## Scope

The current version intentionally keeps the ADB layer small. Device selection, richer error
messages, timeouts, structured command results, fastboot, installation, logs, screenshots, and
file transfer are possible future recipes rather than current features.

# Android Cookbook

Learn to inspect Android devices with Android Debug Bridge (ADB) and Python. This project
covers device discovery, shell commands, and system properties, with unit tests and tests
that run on an emulator or physical device.

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
```

The command selects the first online device. For the output fields and examples, see
[Read Android properties](docs/receipes/v0.3-properties.md).

To inspect the shell user, kernel, and root directory, run:

```bash
PYTHONPATH=src poetry run python -m android_cookbook.shell_info
```

**Known issue:** The shell command's `cwd` field currently repeats the kernel information.
See [Shell output](docs/receipes/v0.2-adb-shell.md#5-print-shell-information) for details.

## Run tests

```bash
# Unit tests: no device required
PYTHONPATH=src poetry run pytest tests/unit

# Integration tests: requires ADB and an online device
PYTHONPATH=src poetry run pytest tests/integration -m integration

# All tests
PYTHONPATH=src poetry run pytest
```

Integration tests use the first online device and skip if none is connected. If ADB is
missing or a command fails, the tests report an error.

## Find your way around

| Path | Contents |
| --- | --- |
| `src/android_cookbook/adb.py` | ADB execution and device discovery |
| `src/android_cookbook/shell.py` | Shell commands and output handling |
| `src/android_cookbook/properties.py` | Property reads, parsing, and collection |
| `src/android_cookbook/device_info.py` | Device properties as JSON |
| `src/android_cookbook/shell_info.py` | Shell information as JSON |
| `tests/unit/` | Tests that replace ADB calls with sample responses |
| `tests/integration/` | Tests that run commands on a device |
| `scripts/health_check.sh` | ADB and emulator environment check |

## Learn more

- [Set up your environment](docs/environment.md)
- [Understand the architecture](docs/architecture.md)
- [v0.1: Run ADB from Python](docs/receipes/v0.1-adb-basics.md)
- [v0.2: Inspect the Android shell](docs/receipes/v0.2-adb-shell.md)
- [v0.3: Read Android properties](docs/receipes/v0.3-properties.md)
- [Roadmap](Roadmap.md)
- [Commit checklist](CommitManual.md)

## Limitations

The JSON commands always use the first online device and have no device-selection option.
ADB calls have no timeout. Property collection requires an SDK value that Python can convert
to an integer. See [Architecture](docs/architecture.md) for error handling and parser behavior.

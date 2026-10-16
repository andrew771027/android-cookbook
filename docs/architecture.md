# Architecture

The Python modules build ADB commands, parse their output, and print device reports as JSON.
Package, property, and general shell commands pass through `run_adb()` in `adb.py`.
Activity Manager uses its own `run_command()` to retain exit status, stdout, and stderr.

```mermaid
flowchart TD
    ActivityManager["activity_manager.py"] --> RunCommand["run_command()"]
    RunCommand --> Subprocess
    DeviceInfo["device_info.main()"] --> Properties["properties.py"]
    PackageLifecycle["run_package_lifecycle()"] --> PackageManager
    PackageInfo["package_info.main()"] --> PackageManager["package_manager.py"]
    PackageManager --> Shell
    PackageManager --> Adb
    Properties --> Shell["shell.py"]
    ShellInfo["shell_info.main()"] --> Shell
    Shell --> Adb["adb.py"]
    CollectDeviceInfo["collect_device_info()"] --> Adb
    Adb --> Subprocess["subprocess.run"]
    Subprocess --> Client["adb client"]
    Client --> Server["adb server"]
    Server --> Device["Android device"]
```


The diagram shows property, shell, and package command paths. All three `main()` functions also call
`adb.list_devices()` to choose the first device whose state is `device`.

## Modules

| Module | Responsibility |
| --- | --- |
| [`activity_manager.py`](../src/android_cookbook/activity_manager.py) | Start activities, force-stop packages, query process IDs, and collect activity diagnostics |
| [`adb.py`](../src/android_cookbook/adb.py) | Run ADB, list devices, and provide the original property reader |
| [`shell.py`](../src/android_cookbook/shell.py) | Run commands on a selected device and parse shell output |
| [`package_manager.py`](../src/android_cookbook/package_manager.py) | Query packages and APK paths; install, uninstall, clear, enable, and disable apps |
| [`package_lifecycle.py`](../src/android_cookbook/package_lifecycle.py) | Sequence package operations and return lifecycle observations |
| [`package_info.py`](../src/android_cookbook/package_info.py) | Select a device and print a package report as JSON |
| [`properties.py`](../src/android_cookbook/properties.py) | Read and parse properties; collect a device report |
| [`device_info.py`](../src/android_cookbook/device_info.py) | Select a device and print its properties as JSON |
| [`shell_info.py`](../src/android_cookbook/shell_info.py) | Select a device and print shell information as JSON |

### ADB execution

`run_adb(*args)` calls `subprocess.run(["adb", *args], capture_output=True, text=True,
check=True)`. It returns standard output with surrounding whitespace removed.

`list_devices()` reads `adb devices` output. It skips the header, blank lines, and rows with
fewer than two columns. Each accepted row becomes an `AdbDevice(serial, state)`.
Offline and unauthorized devices remain in the list; callers decide which state to use.

### Shell commands

`run_shell(serial, *command)` adds `-s <serial> shell` before the command arguments.
For example:

```python
run_shell("emulator-5554", "uname", "-a")
```

runs `adb -s emulator-5554 shell uname -a` and returns a `ShellResult` with two fields:

- `command`: the arguments joined with spaces, such as `uname -a`.
- `output`: the text returned by `run_adb()`.

The joined string is for display. Process execution uses the argument list.

| Helper | Command | Result |
| --- | --- | --- |
| `get_working_directory()` | `pwd` | String |
| `get_current_user()` | `whoami` | String |
| `get_kernel_info()` | `uname -a` | String |
| `list_root_directory()` | `ls /` | List of stripped, non-empty lines |

### Property reads

`properties.get_property(serial, name)` runs `getprop <name>` through `run_shell()` and
strips its output. `get_all_properties(serial)` runs `getprop` once and parses the listing.

`collect_device_properties(serial)` makes eight separate property reads and returns
`DeviceProperties`. It converts `sdk_level` with `int()` and leaves the other values as
strings. It does not cache results or use the bulk listing. See the
[property reference](receipes/v0.3-properties.md#common-properties) for field mappings.

The older `adb.get_property(serial, property_name)` calls `run_adb()` directly. It remains
in use by `collect_device_info()` and the v0.1 tests.

### Property parsing

The parsing functions do not call ADB:

- `parse_properties(output)` strips each line, skips blank lines, and calls
  `parse_property_line()`. It keeps accepted entries in order, including duplicate names.
- `parse_property_line(line)` requires a leading `[` and the exact separator `]: [`.
  It splits at the first separator, removes the opening bracket from the name, and removes
  a final `]` from the value if present. It returns `None` when either initial check fails.

The parser accepts empty names, empty values, and missing closing brackets. When called
directly, `parse_property_line()` does not strip surrounding whitespace.

`AdbDevice`, `ShellResult`, `AndroidProperty`, and `DeviceProperties` are frozen dataclasses:
their fields cannot be reassigned after creation. `ProcessInfo` is also defined in `shell.py`
but is not used.

### Package management

`list_packages()` builds `pm list packages` with optional `-s`, `-3`, `-e`, `-d`, and a
name filter, then calls `run_shell()`. Mutually exclusive system/third-party or
enabled/disabled filters raise `ValueError` before execution. `package_exists()` uses the
filtered listing and compares full names for an exact match.

`parse_package_line()` strips whitespace and requires `package:` followed by a non-empty
name. `parse_package_list()` skips rejected lines and preserves order and duplicates.
`parse_package_paths()` applies the same prefix and non-empty checks to paths and returns
`PackagePath(package_name, paths)`, including all split APK paths. These parsers do not
validate package-name syntax or check whether a path exists.

`get_package_path()`, `clear_package()`, `enable_package()`, and
`disable_package_for_user()` issue `pm` commands through `run_shell()`. Clear returns a
Boolean based on an exact `Success` response; enable and disable return stripped output.
Only the disable helper exposes `user_id`, defaulting to `0`.

`install_apk()` checks that the host path exists, then calls `run_adb()` with
`-s <serial> install`, optional `-r`, `-t` (`allow_test_packages=True`), and `-g`, and the path. `uninstall_package()` calls
`run_adb()` with `-s <serial> uninstall`, optional `-k`, and the package name.
Both return stripped standard output. They do not catch command failures.

`PackageInfo` and `PackagePath` are frozen dataclasses. Fields cannot be reassigned,
though the list stored in `PackagePath.paths` can still be modified.
See the [package recipe](receipes/v0.4-package-manager.md) for commands and return values.

### Package lifecycle

`run_package_lifecycle(serial, apk_path, package_name)` calls package manager helpers in
this order: install with `replace=True` and `allow_test_packages=True`, check existence, read APK paths, clear, check
existence, uninstall without retaining data, and check absence. It returns a frozen
`PackageLifecycleResult` containing the package name, APK paths, and five Boolean observations.
The path list remains mutable. Installation output is ignored; the uninstall flag requires
stripped output to equal `Success`.

The helper does not assert success, validate the APK package name, or provide a CLI.
Exceptions pass through, and there is no guaranteed cleanup if a command raises before
uninstallation. Integration fixtures provide separate setup and teardown around tests.
See the [lifecycle recipe](receipes/v0.4.1-package-lifecycle.md) for fields and examples.

### Activity Manager

`activity_manager.py` calls `subprocess.run()` directly through `run_command()` with
`check=False`, UTF-8 decoding, and replacement of invalid bytes. It uses argument lists
without a host shell and returns a frozen `CommandResult` with `args`, `returncode`,
`stdout`, and `stderr`. `_adb_shell()` adds `adb -s <serial> shell` and rejects blank serials.

`start_activity()` builds `am start [-S] -W -n <package>/<activity>` and combines stdout
and stderr for parsing. Success requires exit code zero, `Status: ok`, and no matching
error line. It returns a frozen `ActivityStartResult`; missing or non-integer timing
fields become `None`. Launch failures raise `ActivityManagerError`.

`force_stop_package()` runs `am force-stop` and returns `None`. `get_process_ids()` runs
`pidof` for the exact process name and returns integer PIDs. A nonzero exit with both
streams empty returns `[]`; other nonzero exits and non-integer PID output raise
`ActivityManagerError`. `is_process_running()` converts that list to a Boolean.
`get_activity_dump()` returns raw stdout from `dumpsys activity activities`.
Force-stop and dump commands raise `ActivityManagerError` on nonzero exit.

Package identifiers are validated before package operations, and `make_component()`
accepts a single relative activity name such as `.MainActivity`. The current regexes
use `[A-Za-z0-0_]` for trailing characters in package segments after the first and in
activity names, so digits 1–9 are rejected there. Fully qualified activity names and
nested relative names are also rejected. These are implementation limits, not a complete
Android component-name validator. See the [recipe](receipes/v0.5.0-activity-manager.md).

### Test APK build flow

The Android project in `fixtures/test-app` supplies the disposable package used by
integration tests. `scripts/build-test-apk.sh` runs `./gradlew assembleDebug` in that
project, then copies `app/build/outputs/apk/debug/app-debug.apk` to
`tests/fixtures/test-app/cookbook-test-app.apk`. The APK is generated locally and ignored
by Git. Building requires JDK 17 and the Android Environment SDK with Platform 36 and
Build Tools 36.0.0; running the tests also requires an online Android device.
See [Build the test APK](receipes/v0.4.2-test-apk-fixture.md#build-the-test-apk).

## JSON commands

All three entry points select the first online device. If none is available, they raise
`RuntimeError("No Android device available")`.

`device_info.main()` calls `collect_device_properties()`, converts the result with `asdict()`,
adds `serial`, and prints indented JSON. The output includes the integer field `sdk_level`.
See the [JSON example](receipes/v0.3-properties.md#4-print-json).

The older `collect_device_info()` helper returns string fields `serial`, `model`,
`android_version`, `sdk`, and `build`. The entry point no longer calls it.

`shell_info.main()` prints `serial`, `user`, `cwd`, `kernel`, and `root_directories`.
It currently calls `get_kernel_info()` for both `cwd` and `kernel`, so those fields contain
the same kind of output. The working-directory helper is implemented but is not called here.

`package_info.main()` requires `--package`, selects an online device, and calls
`package_exists()`. It reads paths only for an installed package and prints `serial`,
`package`, `installed`, and `apk_paths`. An absent package has `installed: false` and an
empty path list. See the [package JSON example](receipes/v0.4-package-manager.md#3-print-a-package-report).

## Error handling

Errors pass through to the caller:

| Condition | Exception |
| --- | --- |
| ADB executable is missing | `FileNotFoundError` |
| ADB exits with a non-zero status | `subprocess.CalledProcessError` |
| APK path does not exist on the workstation | `FileNotFoundError` |
| Package filters conflict | `ValueError` |
| Required `--package` argument is omitted | `argparse` exits with status 2 |
| SDK output cannot be converted to an integer | `ValueError` |
| A JSON command finds no online device | `RuntimeError` |

ADB calls have no timeout. The JSON commands have no option for choosing a serial;
the Python helpers accept one explicitly.

## Tests

Unit tests replace process or device calls with sample responses. Integration tests run
ADB against an online device; shared destructive fixtures require `ANDROID_SERIAL`.

| Test file | Checks |
| --- | --- |
| `tests/unit/test_activity_manager.py` | Component validation, launch parsing and command flags, launch/force-stop errors, PID lookup, and diagnostics |
| `tests/integration/test_activity_manager.py` | Five destructive tests: launch, process creation, force-stop without uninstall, restart, and non-empty diagnostics |
| `tests/unit/test_adb.py` | Device parsing, offline state, and property command arguments |
| `tests/unit/test_shell.py` | Shell arguments, result fields, user, working directory, and root entries |
| `tests/unit/test_properties.py` | Property parsing, read arguments, output trimming, and collection with an integer SDK |
| `tests/unit/test_package_manager.py` | Package parsing, list arguments, conflicting filters, existence, APK paths, clear responses, install options, missing APKs, and basic uninstall |
| `tests/unit/test_package_lifecycle.py` | Successful result and package operation order with mocked helpers |
| `tests/unit/test_package_lifecycle_state_machine.py` | Generated install/enable/disable/clear/uninstall sequences against an in-memory fake; 100 examples × up to 30 steps |
| `tests/integration/test_package_lifecycle_state_machine.py` | Same intended model against real package manager helpers; 3 examples × up to 5 steps; skips for a missing/empty APK or no online device |
| `tests/integration/test_package_lifecycle.py` | Install, APK paths, clear without removal, uninstall, and full sequence; requires the built fixture APK and an online device |
| `tests/integration/test_package_manager.py` | Package listing, Settings existence and APK paths, and system packages |
| `tests/integration/test_device.py` | Device discovery and numeric SDK output |
| `tests/integration/test_shell.py` | Shell user, Linux kernel output, and a `system` root entry |
| `tests/integration/test_properties.py` | Model, SDK, Android version, property listing, and collected report |

Integration modules use `pytest.mark.integration`. Read-only tests skip if no device is
online; shared destructive fixtures skip if `ANDROID_SERIAL` is unset, is not an emulator
serial, or does not report state `device`.
Missing ADB or failed commands cause errors.

The suite does not directly test the JSON entry points, SDK conversion failures, or every
malformed property format. The bulk-property unit test checks parsed output but does not
assert command arguments. For commands to run the tests, see [Run tests](../README.md#run-tests).

Package manager integration tests only query device state and assume `com.android.settings` exists.
They do not test app mutations. Package unit tests do not directly cover enable/disable,
enabled/disabled flag construction, exact-name versus substring matching, or uninstalling
with `keep_data=True`. The package JSON entry point is also untested.

The five fixed-sequence lifecycle integration tests call package manager helpers directly, rather than the lifecycle
helper. Their shared fixtures select an online `emulator-*` serial from `ANDROID_SERIAL` and
check APK existence once per session. Function-scoped cleanup rejects a pre-existing
fixture package, then attempts force-stop and uninstallation in nested `finally` blocks.
Uninstallation is attempted even if force-stop fails; cleanup failures remain visible. The generated APK comes from `fixtures/test-app` through `scripts/build-test-apk.sh`
and is ignored by Git. Tests skip if the expected APK is missing or no device is online.
All five carry `integration` and `destructive` markers. `pytest.ini` excludes destructive
tests by default; select `-m "integration and destructive"` to run them.
The lifecycle unit tests do not cover false results or exceptions. See the
[lifecycle test instructions](receipes/v0.4.1-package-lifecycle.md#5-run-the-tests).

The two lifecycle state machine tests separately define equivalent intended transitions
for `NOT_INSTALLED`, `ENABLED`, and `DISABLED`. Hypothesis generates valid rule sequences
and checks package presence and enabled/disabled listings against that model. The unit
test exercises `FakePackageManager` in memory, so it does not test production ADB behavior.
The integration test calls real package manager helpers, checks for a non-empty APK before
device discovery, and resets the disposable package before and after each example using
its own initialization and `teardown()`. It conditionally calls `pytest.skip()` if the APK is missing or empty; providing a valid
APK and online device enables it automatically.
The `100 × 30` and `3 × 5` settings are example/step budgets, not fixed transition counts.
See the [state machine recipe](receipes/v0.4.1-package-lifecycle.md#6-test-the-package-lifecycle-as-a-state-machine).

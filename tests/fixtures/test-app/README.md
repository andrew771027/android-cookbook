# Android Cookbook test APK

This directory receives the APK used by the
[v0.4.1 package lifecycle tests](../../../docs/receipes/v0.4.1-package-lifecycle.md).
The generated APK is ignored by Git. Build it locally before running device tests.

## Build the APK

Prepare JDK 17, Gradle 9.3.1, and the Android Environment SDK with Platform 36 and
Build Tools 36.0.0. Follow the
[step-by-step build guide](../../../docs/receipes/v0.4.2-test-apk-fixture.md#build-the-test-apk)
for setup, then run from the repository root:

```bash
./scripts/build-test-apk.sh
```

The script builds the Android project in `fixtures/test-app` and copies its debug APK
to `tests/fixtures/test-app/cookbook-test-app.apk`. Its package name is
`com.example.androidcookbook.fixture`, and it requires Android API 31 or later.
In v0.5.0, the app exports `.MainActivity` with a launcher intent filter and displays
“Android Cookbook Activity Fixture”. It requests no application permissions and has no
network behavior. It also supports the [Activity Manager tests](../../../docs/receipes/v0.5.0-activity-manager.md).

In v0.5.1, each Activity instance logs callbacks with tag `CookbookLifecycle`, marker
`android-cookbook-v0.5.1`, and a UUID. A foreground Activity handles the Boolean
`cookbook_finish` extra in `onNewIntent()` and calls `finish()`. See the
[Activity lifecycle recipe](../../../docs/receipes/v0.5.1-activity-lifecycle.md).
The v0.5.2 fixture introduced a counter and orientation display, saves the counter in a
Bundle, and logs `created`, `resumed`, `saved`, `incremented`, and `reported` state events
with tag `CookbookState` and marker `android-cookbook-v0.5.2`. Lifecycle logs retain
the v0.5.1 marker; both tags share the instance UUID. The foreground
Activity accepts `cookbook_action=increment` or `report`. See
[Activity recreation](../../../docs/receipes/v0.5.2-activity-recreation.md). Rotation tests
change system settings and attempt to restore the captured values during teardown.

The current fixture version is v0.5.3 (`versionCode=5`). State logs append
`pid=<Process.myPid()>` while retaining the v0.5.2 marker. The process recovery parser
requires this field; an older APK can install successfully and still cause state-event
timeouts. Only `created` reports whether `savedInstanceState` was received.
See [Process recovery](../../../docs/receipes/v0.5.3-process-death-recovery.md).

Rotation tests establish portrait after Activity launch using `wm user-rotation lock 0`,
then wait for the portrait event before incrementing. Their setup may itself recreate
the Activity. See the [rotation fix](../../../docs/receipes/v0.5.2-activity-recreation.md#v053-rotation-fix-root-cause-and-solution).

Rebuild with `./scripts/build-test-apk.sh` after source changes so tests install the updated APK.

## Run the device tests

Start the Android Environment emulator and confirm it appears in `adb devices -l`.
Select a dedicated emulator, then opt in to destructive tests:

```bash
export ANDROID_SERIAL=emulator-5554
PYTHONPATH=src poetry run pytest \
  tests/integration/test_package_lifecycle.py \
  tests/integration/test_package_lifecycle_state_machine.py \
  tests/integration/test_activity_manager.py \
  tests/integration/test_activity_lifecycle.py \
  tests/integration/test_activity_recreation.py \
  tests/integration/test_process_recovery.py -m "integration and destructive" -v
```

The tests install, inspect, clear, and uninstall the app. The state machine also checks
its enabled and disabled states. Activity lifecycle tests clear Logcat and verify launch,
Home, return from Home, and graceful finish. Run them sequentially on a dedicated emulator.
Process recovery tests also request background process death and restore the saved task
using matching MAIN/LAUNCHER intents with `NEW_TASK | RESET_TASK_IF_NEEDED`.
Tests use `allow_test_packages=True` to pass ADB's
`-t` option when installing the test APK.

The fixed-sequence fixture skips when the APK is missing; the state machine also skips
if it is empty. The shared fixed-sequence fixtures also require `ANDROID_SERIAL` to select an online
`emulator-*` device. The state machine independently selects the first online device. An invalid, non-empty APK can still
fail at installation. No skip decorators need to be removed.

Shared fixtures fail if the package is already installed, then force-stop and uninstall
after each test. The state machine removes existing installations before and after each
example. Default pytest commands exclude these destructive tests. Use a disposable
emulator because clearing or uninstalling the app deletes its data. Unit tests use a
simulated Android backend and do not need this APK or a device.

## Before committing

The file-specific command above checks the fixture consumers during development. Before
committing, rebuild this APK, then run all unit tests and the complete integration suite:

```bash
PYTHONPATH=src poetry run pytest tests/unit
PYTHONPATH=src poetry run pytest tests/integration -m integration -v -rs
```

Follow the [commit checklist](../../../CommitManual.md#run-the-full-integration-suite)
for emulator setup and removal of existing installations. Only the dedicated emulator
should be online; run sequentially. Require all tests to pass without skips or
deselected tests, and verify that cleanup leaves the fixture package absent. Missing
APK or device prerequisites must be resolved before committing.

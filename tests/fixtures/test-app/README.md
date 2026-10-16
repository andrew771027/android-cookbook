# Package lifecycle test APK

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

## Run the device tests

Start the Android Environment emulator and confirm it appears in `adb devices -l`.
Select a dedicated emulator, then opt in to destructive tests:

```bash
export ANDROID_SERIAL=emulator-5554
PYTHONPATH=src poetry run pytest \
  tests/integration/test_package_lifecycle.py \
  tests/integration/test_package_lifecycle_state_machine.py \
  tests/integration/test_activity_manager.py -m "integration and destructive" -v
```

The tests install, inspect, clear, and uninstall the app. The state machine also checks
its enabled and disabled states. Tests use `allow_test_packages=True` to pass ADB's
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

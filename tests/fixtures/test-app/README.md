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
The app has no UI, application permissions, or network behavior.

## Run the device tests

Start the Android Environment emulator and confirm it appears in `adb devices -l`.
Then run:

```bash
PYTHONPATH=src poetry run pytest \
  tests/integration/test_package_lifecycle.py \
  tests/integration/test_package_lifecycle_state_machine.py -v
```

The tests install, inspect, clear, and uninstall the app. The state machine also checks
its enabled and disabled states. Tests use `allow_test_packages=True` to pass ADB's
`-t` option when installing the test APK.

The fixed-sequence fixture skips when the APK is missing; the state machine also skips
if it is empty. Both skip when no device is online. An invalid, non-empty APK can still
fail at installation. No skip decorators need to be removed.

Setup and cleanup remove any existing installation of this package. Use a disposable
emulator because clearing or uninstalling the app deletes its data. Unit tests use a
simulated Android backend and do not need this APK or a device.

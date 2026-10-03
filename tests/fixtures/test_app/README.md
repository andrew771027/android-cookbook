# Package lifecycle test app

This directory holds the disposable APK used by the
[v0.4.1 package lifecycle tests](../../../docs/receipes/v0.4.1-package-lifecycle.md).
The checked-in `cookbook-test-app.apk` is an empty placeholder, not an installable app.

## Provide an APK

Build or supply a test app with package name `com.example.androidcookbook.fixture` and
save it as `tests/fixtures/test_app/cookbook-test-app.apk` from the repository root.
The APK must support the Android API level of the device used for testing.
No app source or APK build command is provided in this repository.

Use an app that contains no personal data, requires no account or network access, and
can safely be cleared and uninstalled. The integration fixtures remove any existing
installation with this package name before and after each test.

## What the tests do

The lifecycle tests install the APK, inspect its paths, clear its data, verify that it
remains installed, and uninstall it. The package manager API also exposes reinstallation,
enabling, and disabling. The fixed-sequence lifecycle tests do not exercise enable/disable;
the new lifecycle state machine tests include both operations.

The APK fixture checks only that the file exists. An empty or invalid APK is passed to
ADB and fails during installation. All five lifecycle integration tests currently have
unconditional `skip` markers, so their fixtures and device operations do not run.
Provide a valid APK and remove those markers to enable the tests; see the recipe for
commands and how to interpret their results.

The state machine unit test uses an in-memory `FakePackageManager` and a fake APK path;
it does not read this APK and runs without an Android device. The state machine integration
test checks that this APK exists and is non-empty before device discovery, and calls
`pytest.skip()` while the checked-in placeholder is empty. A non-empty file alone does
not establish APK validity. Supply a valid APK and connect an online device to enable
that test without changing a skip decorator. Each generated example removes the fixture
package before its rules and again during teardown. See the
[state machine recipe](../../../docs/receipes/v0.4.1-package-lifecycle.md#6-test-the-package-lifecycle-as-a-state-machine).

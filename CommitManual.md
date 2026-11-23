# Commit checklist

Before every commit, complete the code, test, and documentation checks below.
Review release checks as applicable.

## Code and tests

- [ ] Review the diff for unintended changes.
- [ ] Check that tests cover any behavior you changed.
- [ ] Rebuild the fixture APK with `./scripts/build-test-apk.sh`. For v0.5.4, confirm
  the fixture version is `0.5.4` (`versionCode=6`) and `CookbookState` logs include `pid`; an older APK without it cannot satisfy the
  process recovery parser even though the state marker remains v0.5.2.
- [ ] Prepare an online dedicated emulator and remove any existing fixture installation.
- [ ] Run `make test` to execute the full unit and integration suites, including destructive tests.
- [ ] Confirm every unit and integration test passed, with no failures, errors, skips,
  or deselected tests. Resolve missing devices, APKs, or other prerequisites and rerun
  before committing. A run with skipped or deselected tests is incomplete verification.
- [ ] Run `git diff --check`.

### Run the full integration suite

Run from the repository root with only the dedicated test emulator online. Some tests
select the first online device instead of using `ANDROID_SERIAL`.

```bash
./scripts/build-test-apk.sh
export ANDROID_SERIAL=emulator-5554
adb devices -l
adb -s "$ANDROID_SERIAL" get-state
adb -s "$ANDROID_SERIAL" shell pm list packages com.example.androidcookbook.fixture
```

Verify the selected emulator reports `device`. If the package listing contains
`package:com.example.androidcookbook.fixture`, remove it before testing:

```bash
adb -s "$ANDROID_SERIAL" uninstall com.example.androidcookbook.fixture
```

Run the full test suite sequentially with the prepared emulator.

```bash
make test
```

`make test` clears the default `not destructive` filter in `pytest.ini` with `-m ""`
and reports any skip reasons.

These tests install, clear, enable, disable, force-stop, and uninstall the disposable
fixture app. Activity lifecycle tests also clear the shared Logcat buffer and change
the foreground Activity. Process recovery tests also background the fixture, request
`am kill`, verify process absence, and relaunch its task to check saved state. A skip
because Android refused to kill the process is incomplete verification.

Launch diagnostics tests also establish cold, warm, and hot scenarios by force-stopping,
gracefully finishing, or backgrounding the fixture Activity. Warm and hot tests skip if
the original process does not survive setup. Such skips are incomplete verification.
Review the [v0.5.4 known limitations](docs/receipes/v0.5.4-activity-launch-diagnostics.md#known-limitations)
before treating passing tests as complete launch validation.

Keep the emulator unlocked and avoid other automation during
the run. Activity recreation tests also modify `accelerometer_rotation` and
`user_rotation`; their fixture captures and attempts to restore both settings. Confirm
the original rotation settings are restored after testing. Rotation tests now apply
`wm user-rotation lock 0` after Activity launch and wait for the portrait baseline;
see the [v0.5.3 rotation root cause and solution](docs/receipes/v0.5.2-activity-recreation.md#v053-rotation-fix-root-cause-and-solution).
Confirm teardown leaves the fixture package absent.

## Documentation

- [ ] Check every document under `docs/` against the current source, tests, and build
  configuration. Correct any outdated behavior descriptions, commands, examples,
  prerequisites, or test coverage and skip conditions before committing.
- [ ] Docs should be Google like, human readable not AI generated
- [ ] Update [README.md](README.md) if setup, commands, or output changed.
- [ ] Update [Architecture](docs/architecture.md) if module responsibilities or data flow changed.
- [ ] Update [Environment setup](docs/environment.md) if dependencies or setup steps changed.
- [ ] Update the relevant [recipe](README.md#learn-more), including commands and example output.
- [ ] Update [Roadmap](Roadmap.md) when a planned topic becomes available.

## Release changes

- [ ] Check the package version in `pyproject.toml`.
- [ ] Create the release tag when publishing a release.

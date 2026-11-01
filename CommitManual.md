# Commit checklist

Before every commit, complete the code and test checks below. Review documentation
and release checks as applicable.

## Code and tests

- [ ] Review the diff for unintended changes.
- [ ] Check that tests cover any behavior you changed.
- [ ] Run `PYTHONPATH=src poetry run pytest tests/unit`.
- [ ] Rebuild the fixture APK with `./scripts/build-test-apk.sh`.
- [ ] Prepare an online dedicated emulator and remove any existing fixture installation.
- [ ] Run the full integration suite, including destructive tests, using the commands below.
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

Run all integration tests sequentially, without file filters, `-k`, or parallel workers:

```bash
PYTHONPATH=src poetry run pytest tests/integration -m integration -v -rs
```

The explicit `-m integration` overrides the `not destructive` filter in `pytest.ini`
and includes both read-only and destructive integration tests. Running
`PYTHONPATH=src poetry run pytest tests/integration` without this override excludes
destructive tests and does not satisfy the commit requirement. A targeted test run
also does not replace the full suite.

These tests install, clear, enable, disable, force-stop, and uninstall the disposable
fixture app. Activity lifecycle tests also clear the shared Logcat buffer and change
the foreground Activity. Keep the emulator unlocked and avoid other automation during
the run. Activity recreation tests also modify `accelerometer_rotation` and
`user_rotation`; their fixture captures and attempts to restore both settings. Confirm
the original rotation settings are restored after testing. Confirm teardown leaves the fixture package absent.

## Documentation

- [ ] Docs should be Google like, human readable not AI generated
- [ ] Update [README.md](README.md) if setup, commands, or output changed.
- [ ] Update [Architecture](docs/architecture.md) if module responsibilities or data flow changed.
- [ ] Update [Environment setup](docs/environment.md) if dependencies or setup steps changed.
- [ ] Update the relevant [recipe](README.md#learn-more), including commands and example output.
- [ ] Update [Roadmap](Roadmap.md) when a planned topic becomes available.

## Release changes

- [ ] Check the package version in `pyproject.toml`.
- [ ] Create the release tag when publishing a release.

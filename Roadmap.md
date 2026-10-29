# Roadmap

Android Cookbook starts with ADB commands and Python wrappers, then builds toward device
inspection, testing, and automation.

## Available recipes

| Recipe | What you can learn |
| --- | --- |
| [v0.1: ADB basics](docs/receipes/v0.1-adb-basics.md) | Discover devices and read a property |
| [v0.2: ADB shell](docs/receipes/v0.2-adb-shell.md) | Run shell commands and inspect their output |
| [v0.3: Android properties](docs/receipes/v0.3-properties.md) | Parse properties and collect device information |
| [v0.4: Package manager](docs/receipes/v0.4-package-manager.md) | Discover packages, inspect APK paths, and manage test apps |
| [v0.4.1: Package lifecycle](docs/receipes/v0.4.1-package-lifecycle.md) | Combine package operations and use fixtures for device setup and cleanup |
| [v0.4.2: Test APK fixture](docs/receipes/v0.4.2-test-apk-fixture.md) | Set up Android build tools, build a disposable APK, and validate it on an emulator |
| [v0.5.0: Activity Manager](docs/receipes/v0.5.0-activity-manager.md) | Launch an Activity, inspect its process, force-stop, restart, and collect diagnostics |
| [v0.5.1: Activity lifecycle](docs/receipes/v0.5.1-activity-lifecycle.md) | Observe callbacks through Logcat and verify launch, Home, return, and graceful finish for one Activity instance |

| [v0.5.2: Activity recreation](docs/receipes/v0.5.2-activity-recreation.md) | Rotate the emulator, correlate Activity instances, and verify saved counter restoration |

Recipe numbers describe the learning sequence. The package version in `pyproject.toml`
is currently `0.5.2`.

## Planned topics

The following topics are planned. Version assignments remain open after the addition of
the v0.5.2 Activity recreation recipe.

| Topic | Commands and concepts |
| --- | --- |
| File system | `/data`, `/sdcard`, and permissions |
| Android services | Inspect service state with `dumpsys` |
| Logcat streaming | Extend the v0.5.1 buffer snapshots with streaming and process filters |
| System configuration | Read and change settings with `settings` and `svc` |
| File transfer | Copy files with `adb push` and `adb pull` |
| Fastboot | Understand the bootloader and fastboot commands |

## Longer-term direction

- **v1.x:** Android system inspection
- **v2.x:** Android test recipes
- **v3.x:** Device validation recipes
- **v4.x:** Automation and continuous integration

# Roadmap

Android Cookbook starts with ADB commands and Python wrappers, then builds toward device
inspection, testing, and automation.

## Available recipes

| Recipe | What you can learn |
| --- | --- |
| [v0.1: ADB basics](docs/receipes/v0.1-adb-basics.md) | Discover devices and read a property |
| [v0.2: ADB shell](docs/receipes/v0.2-adb-shell.md) | Run shell commands and inspect their output |
| [v0.3: Android properties](docs/receipes/v0.3-properties.md) | Parse properties and collect device information |

Recipe numbers describe the learning sequence. The package version in `pyproject.toml`
is currently `0.1.0`.

## Planned topics

The following topics are planned. Version assignments remain open after the addition of
the v0.3 properties recipe.

| Topic | Commands and concepts |
| --- | --- |
| File system | `/data`, `/sdcard`, and permissions |
| Package manager | List, install, and uninstall packages with `pm` |
| Activity manager | Start activities and stop apps with `am` |
| Android services | Inspect service state with `dumpsys` |
| Logcat | Collect logs and filter by process |
| System configuration | Read and change settings with `settings` and `svc` |
| File transfer | Copy files with `adb push` and `adb pull` |
| Fastboot | Understand the bootloader and fastboot commands |

## Longer-term direction

- **v1.x:** Android system inspection
- **v2.x:** Android test recipes
- **v3.x:** Device validation recipes
- **v4.x:** Automation and continuous integration

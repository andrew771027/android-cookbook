# Android Cookbook Test Application

This directory contains the disposable Android application
used by package lifecycle integration tests.

## Package Name

```text
com.example.androidcookbook.fixture

Purpose
The application exists only for testing Android Package
Manager operations.
It may be:
- installed
- reinstalled
- cleared
- disabled
- enabled
- uninstalled
Do not use a production application as this fixture.
Requirements
The APK must:
- use the fixed package name
- contain no user data
- require no account
- require no network access
- be safe to uninstall
- support the Android API level used by Android Environment
Expected File
tests/fixtures/test_app/cookbook-test-app.apk

Lifecycle
APK
 |
 | adb install
 v
Installed Package
 |
 | pm clear
 v
Installed Package / Clean Data
 |
 | adb uninstall
 v
Removed

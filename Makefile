ANDROID_SERIAL ?= emulator-5554
export ANDROID_SERIAL

.PHONY: \
	exec_device_info \
	exec_package_info \
	cleanup_apk \
	init_android_serial \
	build_apk \
	test \
	test_unit \
	test_integration \
	test_all_integration

exec_device_info:
	@PYTHONPATH=src poetry run python3 -m android_cookbook.device_info

exec_package_info:
	@PYTHONPATH=src poetry run python3 -m android_cookbook.package_info --package com.android.settings

cleanup_apk:
	@packages=$$(adb -s "$(ANDROID_SERIAL)" shell pm list packages com.example.androidcookbook.fixture) || exit $$?; \
	if printf '%s\n' "$$packages" | tr -d '\r' | grep -qx 'package:com.example.androidcookbook.fixture'; then \
		adb -s "$(ANDROID_SERIAL)" uninstall com.example.androidcookbook.fixture; \
	else \
		echo "Fixture is already absent from $(ANDROID_SERIAL)."; \
	fi

build_apk:
	bash ./scripts/build-test-apk.sh

init_android_serial:
	@echo "ANDROID_SERIAL=$$ANDROID_SERIAL"

test:
	@PYTHONPATH=src poetry run pytest -v -rs -m "" ./tests

test_unit:
	@PYTHONPATH=src poetry run pytest -v ./tests/unit

test_integration:
	@PYTHONPATH=src poetry run pytest -v -m 'integration and destructive' ./tests/integration


test_all_integration:
	@PYTHONPATH=src poetry run pytest -v -m integration ./tests/integration

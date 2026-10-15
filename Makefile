exec_device_info:
	@PYTHONPATH=src poetry run python3 -m android_cookbook.device_info

exec_package_info:
	@PYTHONPATH=src poetry run python3 -m android_cookbook.package_info --package com.android.settings

test:
	@PYTHONPATH=src poetry run pytest -v ./tests

test_unit:
	@PYTHONPATH=src poetry run pytest -v ./tests/unit

test_integration:
	@PYTHONPATH=src poetry run pytest -v -m integration ./tests/integration

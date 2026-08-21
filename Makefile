exec:
	@PYTHONPATH=src poetry run python3 -m android_cookbook.device_info

test:
	@PYTHONPATH=src poetry run pytest -v ./tests

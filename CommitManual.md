# Commit checklist

Before committing, review the items that apply to your change.

## Code and tests

- [ ] Review the diff for unintended changes.
- [ ] Check that tests cover any behavior you changed.
- [ ] Run `PYTHONPATH=src poetry run pytest tests/unit`.
- [ ] For changes to device commands, run the relevant integration tests on an online device.
- [ ] Run `git diff --check`.

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

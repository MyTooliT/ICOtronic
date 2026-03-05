# -- Settings ------------------------------------------------------------------

# Use latest version of PowerShell on Windows
set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# -- Variables -----------------------------------------------------------------

package := "icotronic"
sphinx_input_directory := "Documentation/Sphinx"
sphinx_directory := "Sphinx"
test_directory := "Test"
# Note: The pytest plugin `pytest-sphinx` (version 0.6.3) does unfortunately not
# find our API documentation doctests, hence we specify the test files (*.rst)
# manually.
sphinx_tests := sphinx_input_directory / "api.rst"
test_locations := package + " " + test_directory

export PYTEST_ADDOPTS := if os() == "windows" { "-p no:prysk" } else { "" }

# -- Recipes -------------------------------------------------------------------

# Setup Python environment
[group('setup')]
setup:
	uv venv --allow-existing
	uv sync --all-extras

# Check code with various linters
[group('lint')]
check: setup
	uv run mypy "{{package}}"
	uv run flake8
	uv run pylint .

# Helper for running tests
[group('test')]
_test *options: check && coverage
	uv run coverage run -m pytest \
		--reruns 5 \
		--reruns-delay 1 \
		--doctest-modules \
		{{options}}

# Run tests
[default]
[group('test')]
test: (_test sphinx_tests test_directory package)

# Run hardware-independent tests
[group('test')]
test-no-hardware: (_test
	"--ignore=Test/Prysk/concurrent_access.t"
	"--ignore=Test/Prysk/read_data.t"
	"--ignore=Test/Prysk/sth_name.t"
	"--ignore=Test/Prysk/store_data.t"
	"--ignore=Test/Prysk/measure.t"
	"--ignore=Test/pytest/test_connect.py"
	"--ignore=Test/pytest/test_streaming.py"
	"--ignore=icotronic/can/connection.py"
	"--ignore=icotronic/can/node/basic.py"
	"--ignore=icotronic/can/node/eeprom/basic.py"
	"--ignore=icotronic/can/node/eeprom/node.py"
	"--ignore=icotronic/can/node/eeprom/sensor.py"
	"--ignore=icotronic/can/node/eeprom/sth.py"
	"--ignore=icotronic/can/node/sensor.py"
	"--ignore=icotronic/can/node/spu.py"
	"--ignore=icotronic/can/node/sth.py"
	"--ignore=icotronic/can/node/stu.py"
	"--ignore=Documentation")

# Print coverage report
[private]
coverage:
	uv run coverage report

# Release new package version
[group('release')]
[unix]
release version:
	#!/usr/bin/env sh -e
	uv version {{version}}
	version="$(uv version --short)"
	git commit -a -m "Release: Release version ${version}"
	git tag "${version}"
	git push
	git push --tags

# Release new package version
[group('release')]
[windows]
release version:
	#!pwsh
	uv version {{version}}
	set version "$(uv version --short)"
	git commit -a -m "Release: Release version ${version}"
	git tag "${version}"
	git push
	git push --tags

# Generate documentation
[group('documentation')]
documentation: setup
	uv run sphinx-apidoc -f -o {{sphinx_directory}} {{sphinx_input_directory}}
	uv run sphinx-build -M html {{sphinx_input_directory}} {{sphinx_directory}}

# Remove documentation
[group('documentation')]
[windows]
clean:
	#!pwsh
	Remove-Item -Recurse {{sphinx_directory}}

# Remove documentation
[group('documentation')]
[unix]
clean:
	#!/usr/bin/env sh -e
	rm -rf {{sphinx_directory}}

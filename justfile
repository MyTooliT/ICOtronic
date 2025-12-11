# -- Settings ------------------------------------------------------------------

# Use latest version of PowerShell on Windows
set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# -- Variables -----------------------------------------------------------------

package := "icotronic"

bookdown_directory := "Bookdown"
pictures_input_directory := "Documentation/Pictures"
pictures_output_directory := "Pictures"
output_name := "Documentation"
index_file := "Documentation/Introduction.md"
html_file := bookdown_directory + "/" + output_name + ".html"

sphinx_input_directory := "Documentation/API"
sphinx_directory := "Sphinx"

test_directory := "Test"
# Note: The pytest plugin `pytest-sphinx` (version 0.6.3) does unfortunately not
# find our API documentation doctests, hence we specify the test files (*.rst)
# manually.
sphinx_tests := sphinx_input_directory / "usage.rst"
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
_test $CI *options: check && coverage
	uv run coverage run -m pytest \
		--reruns 5 \
		--reruns-delay 1 \
		--doctest-modules \
		{{options}}

# Run tests
[default]
[group('test')]
test: (_test "false" sphinx_tests test_directory package)

# Run hardware-independent tests
[group('test')]
test-no-hardware: (_test "true"
	"--ignore-glob='*read_data.t'"
	"--ignore-glob='*sth_name.t'"
	"--ignore-glob='*store_data.t'"
	"--ignore-glob='*measure.t'"
	"--ignore='Documentation'")

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

# =================
# = Documentation =
# =================

# Generate API documentation
[group('documentation')]
documentation-api:
	uv run sphinx-apidoc -f -o {{sphinx_directory}} {{sphinx_input_directory}}
	uv run sphinx-build -M html {{sphinx_input_directory}} {{sphinx_directory}}

# Generate general documentation
[group('documentation')]
documentation-general: init epub html pdf cleanup

# Copy pictures to repository root
[private]
init:
	Rscript -e "dir.create('{{pictures_output_directory}}')"
	Rscript -e "file.copy('{{pictures_input_directory}}', '.', recursive=T)"

# Remove pictures from repository root
[private]
cleanup:
	Rscript -e "unlink('Pictures', recursive = TRUE)"

_epub:
	Rscript -e "bookdown::render_book('{{index_file}}', 'bookdown::epub_book')"

_html:
	Rscript -e "bookdown::render_book('{{index_file}}', 'bookdown::gitbook')"
	Rscript -e \
		"file.rename('{{html_file}}', '{{bookdown_directory}}/index.html')"

_pdf:
	Rscript -e "bookdown::render_book('{{index_file}}', 'bookdown::pdf_book')"

# Create general documentation in EPUB format
[group('documentation')]
epub: init _epub && cleanup

# Create general documentation in HTML format
[group('documentation')]
html: init _html && cleanup

# Create general documentation in PDF format
[group('documentation')]
pdf: init _pdf && cleanup

# Remove generated documentation
[group('documentation')]
clean: cleanup
	Rscript -e "unlink('{{bookdown_directory}}', recursive = TRUE)"
	Rscript -e "unlink('{{sphinx_directory}}', recursive = TRUE)"

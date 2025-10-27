# -- Variables -----------------------------------------------------------------

MODULE := icotronic

BOOKDOWN_DIRECTORY := Bookdown
SPHINX_DIRECTORY := Sphinx
SPHINX_INPUT_DIRECTORY := Documentation/API
INDEX_FILE := Documentation/Introduction.md
OUTPUT_NAME := Documentation

PDF_FILE := $(BOOKDOWN_DIRECTORY)/$(OUTPUT_NAME).pdf
EPUB_FILE := $(BOOKDOWN_DIRECTORY)/$(OUTPUT_NAME).epub
HTML_FILE := $(BOOKDOWN_DIRECTORY)/$(OUTPUT_NAME).html

# Note: The pytest plugin `pytest-sphinx` (version 0.6.3) does unfortunately not
# find our API documentation doctests, hence we specify the test files (*.rst)
# manually.
TEST_LOCATIONS := $(wildcard $(SPHINX_INPUT_DIRECTORY)/*.rst) $(MODULE) Test

ifeq ($(OS), Windows_NT)
	OPERATING_SYSTEM := windows
	# Disable Prysk pytest plugin
	export PYTEST_ADDOPTS := -p no:prysk
else
	OS_NAME := $(shell uname -s)
	ifeq ($(OS_NAME), Linux)
		OPERATING_SYSTEM := linux
	else
		OPERATING_SYSTEM := mac
	endif
endif

# -- Rules ---------------------------------------------------------------------

run: check test


# =========
# = Setup =
# =========

.PHONY: setup
setup:
	uv venv --allow-existing
	uv sync --all-extras

# =========
# = Tests =
# =========

.PHONY: check
check:
	uv run flake8
	uv run mypy $(MODULE)
	uv run pylint .

.PHONY: test
test: pytest-test
	uv run coverage report
test-no-hardware: pytest-test-no-hardware

# ----------
# - Pytest -
# ----------

pytest-test:
	uv run coverage run -m pytest $(TEST_LOCATIONS) || \
	  ( uv run icon stu reset && \
	    uv run coverage run --append -m \
	    pytest --last-failed $(TEST_LOCATIONS) )

pytest-test-no-hardware:
	uv run pytest --ignore-glob='*read_data.t' \
	                  --ignore-glob='*sth_name.t' \
	                  --ignore-glob='*store_data.t' \
	                  --ignore-glob='*measure.t' \
	                  --ignore='Documentation'

# =================
# = Documentation =
# =================

# ------------
# - Bookdown -
# ------------

doc: init $(EPUB_FILE) $(HTML_FILE) $(PDF_FILE) cleanup

# Copy pictures to repository root and create diagrams
init:
	Rscript -e "dir.create('Pictures')"
	Rscript -e "file.copy('Documentation/Pictures', '.', recursive=T)"

# Remove pictures from repository root
cleanup:
	Rscript -e "unlink('Pictures', recursive = TRUE)"

epub: init $(EPUB_FILE) cleanup
html: init $(HTML_FILE) cleanup
pdf: init $(PDF_FILE) cleanup

# Generate EPUB document
$(EPUB_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::epub_book')"

# Generate (GitBook) HTML document
$(HTML_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::gitbook')"
	Rscript -e "file.rename('$(HTML_FILE)', '$(BOOKDOWN_DIRECTORY)/index.html')"

# Generate PDF
$(PDF_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::pdf_book')"

clean: cleanup
	Rscript -e "unlink('$(BOOKDOWN_DIRECTORY)', recursive = TRUE)"
	Rscript -e "unlink('$(SPHINX_DIRECTORY)', recursive = TRUE)"

# -------
# - API -
# -------

.PHONY: doc-api
doc-api:
	uv run sphinx-apidoc -f -o $(SPHINX_DIRECTORY) $(SPHINX_INPUT_DIRECTORY)
	uv run sphinx-build -M html $(SPHINX_INPUT_DIRECTORY) \
	  $(SPHINX_DIRECTORY)

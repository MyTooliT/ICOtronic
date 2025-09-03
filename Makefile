# -- Variables -----------------------------------------------------------------

MODULE := icotronic
STH_TEST := $(MODULE)/test/production/sth.py
STU_TEST := $(MODULE)/test/production/stu.py

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
TEST_LOCATIONS := $(SPHINX_INPUT_DIRECTORY)/usage.rst $(MODULE) Test

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
# = Tests =
# =========

.PHONY: check
check:
	poetry run flake8
	poetry run mypy $(MODULE)
	poetry run pylint .

.PHONY: test
test: pytest-test hardware-test coverage
test-no-hardware: pytest-test-no-hardware

# ----------
# - Pytest -
# ----------

pytest-test:
	poetry run coverage run -m pytest $(TEST_LOCATIONS) || \
	  ( poetry run icon stu reset && \
	    poetry run coverage run --append -m pytest --last-failed )

pytest-test-no-hardware:
	poetry run pytest --ignore-glob='*read_data.t' \
	                  --ignore-glob='*sth_name.t' \
	                  --ignore-glob='*store_data.t' \
	                  --ignore-glob='*measure.t' \
	                  --ignore='Documentation'

# ------------------
# - Hardware Tests -
# ------------------

hardware-test: run-hardware-test open-test-report-$(OPERATING_SYSTEM)

run-hardware-test:
	poetry run coverage run -a $(STH_TEST) -v
	poetry run coverage run -a $(STU_TEST) -v -k eeprom -k connection

open-test-report-windows:
	@powershell -c "Invoke-Item (Join-Path $$PWD 'STH Test.pdf')"
	@powershell -c "Invoke-Item (Join-Path $$PWD 'STU Test.pdf')"

open-test-report-mac:
	@open 'STH Test.pdf' 'STU Test.pdf'

open-test-report-linux:
	@if [ -z "$(DISPLAY)" ]; \
	then \
	  printf "Please check the files “STH Test.pdf” and “STU Test.pdf”\n"; \
	else \
	  xdg-open 'STH Test.pdf'; \
	  xdg-open 'STU Test.pdf'; \
	fi

# ------------
# - Coverage -
# ------------

.PHONY: coverage
coverage:
	poetry run coverage report

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
	poetry run sphinx-apidoc -f -o $(SPHINX_DIRECTORY) $(SPHINX_INPUT_DIRECTORY)
	poetry run sphinx-build -M html $(SPHINX_INPUT_DIRECTORY) \
	  $(SPHINX_DIRECTORY)

"""Sphinx configuration"""

# pylint: disable=invalid-name

# -- Imports ------------------------------------------------------------------

import maisie_sphinx_theme

from icotronic import __version__

# -- Project information ------------------------------------------------------

project = "ICOtronic"
# pylint: disable=redefined-builtin
copyright = "2025, Clemens Burgstaller, René Schwaiger"
# pylint: enable=redefined-builtin
author = "Clemens Burgstaller, René Schwaiger"
release = __version__

# -- General configuration ----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.doctest",
    "sphinx_toggleprompt",
]

# Run doctest from doctest directive, but not nested tests from autodoc code
doctest_test_doctest_blocks = ""

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Autodoc Configuration ----------------------------------------------------

autoclass_content = "both"
autodoc_inherit_docstrings = False

# -- Options for HTML output --------------------------------------------------

html_theme_path = maisie_sphinx_theme.html_theme_path()
html_theme = "maisie_sphinx_theme"
# Register the theme as an extension to generate a sitemap.xml
extensions.append("maisie_sphinx_theme")

# pylint: enable=invalid-name

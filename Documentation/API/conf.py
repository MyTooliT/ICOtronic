# -- Imports ------------------------------------------------------------------

import maisie_sphinx_theme

from icotronic import __version__

# -- Project information ------------------------------------------------------

project = "ICOtronic"
copyright = "2025, Clemens Burgstaller, René Schwaiger"
author = "Clemens Burgstaller, René Schwaiger"
release = __version__

# -- General configuration ----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx_copybutton",
    "sphinx_toggleprompt",
]

# Run doctest from doctest directive, but not nested tests from autodoc code
doctest_test_doctest_blocks = ""

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output --------------------------------------------------

html_theme_path = maisie_sphinx_theme.html_theme_path()
html_theme = "maisie_sphinx_theme"
# Register the theme as an extension to generate a sitemap.xml
extensions.append("maisie_sphinx_theme")

toggleprompt_offset_right = 35

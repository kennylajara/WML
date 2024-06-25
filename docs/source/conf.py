# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
from datetime import date
from pathlib import Path

src = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src))

current_year = date.today().year

project = 'WML'
author = 'Kenny Lajara'
copyright = f'{current_year}, {author}'
release = '0.1.0-alpha'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
]
source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = []

html_css_files = [
    'css/style.css',
]



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

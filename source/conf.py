import datetime

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'OORT'
copyright = f"{datetime.datetime.now().year}, Emre Çalışkan"
author = 'Emre Çalışkan'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = project
html_permalinks_icon = '<span>#</span>'
html_theme = 'sphinxawesome_theme'
html_static_path = ['_static']

html_theme_options = {
   # Add your theme options. For example:
   "show_breadcrumbs": True,
    "show_prev_next": True,
   "main_nav_links": {
      "Github": "https://github.com/thecaliskan/oort",
      "Docker Hub": "https://hub.docker.com/r/thecaliskan/oort",
   }
}
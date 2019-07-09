# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.abspath('..'))
import aiohttp_utils  # noqa

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx_issues',
    'sphinx_autodoc_annotation',
]

primary_domain = 'py'
default_role = 'py:obj'

intersphinx_mapping = {
    'python': ('https://python.readthedocs.io/en/latest/', None),
    'aiohttp': ('https://aiohttp.readthedocs.io/en/stable/', None),
}

issues_github_path = 'sloria/aiohttp_utils'

source_suffix = '.rst'
master_doc = 'index'
project = 'aiohttp_utils'
copyright = 'Steven Loria {0:%Y}'.format(
    dt.datetime.utcnow()
)

version = release = aiohttp_utils.__version__

exclude_patterns = ['_build']

# THEME

# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

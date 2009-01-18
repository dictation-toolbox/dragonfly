# -*- coding: utf-8 -*-
#

import sys, os, os.path, re

directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(directory)


#---------------------------------------------------------------------------
# Gather version from distribution file.

path = os.path.join(directory, "version.txt")
version_string = open(path).readline()
match = re.match(r"\s*(?P<rel>(?P<ver>\d+\.\d+)(?:\.\S+)*)\s*", version_string)
version = match.group("ver")
release = match.group("rel")
print "Version:", version, "-- Release:", release


#---------------------------------------------------------------------------
# General configuration

extensions = ['sphinx.ext.autodoc']
templates_path = ['templates']
source_suffix = '.txt'
master_doc = 'index'

# General substitutions.
project = u'Dragonfly'
copyright = u'2008, Christo Butcher'

today_fmt = '%B %d, %Y'
exclude_trees = []
add_module_names = False # True
pygments_style = 'sphinx'


#---------------------------------------------------------------------------
# Options for HTML output

html_style = 'default.css'
html_static_path = ['static']
html_last_updated_fmt = '%b %d, %Y'
html_copy_source = True
htmlhelp_basename = 'Dragonflydoc'


#---------------------------------------------------------------------------
# Options for LaTeX output

latex_documents = [
  ('index', 'Dragonfly.tex', u'Dragonfly Documentation',
   u'Christo Butcher', 'manual'),
]

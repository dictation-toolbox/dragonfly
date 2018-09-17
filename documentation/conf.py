# -*- coding: utf-8 -*-
#

import sys
import os
import os.path
import re

directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, directory)


#---------------------------------------------------------------------------
# Gather version from distribution file.

path = os.path.join(directory, "version.txt")
version_string = open(path).readline()
match = re.match(r"\s*(?P<rel>(?P<ver>\d+\.\d+)(?:\.\S+)*)\s*", version_string)
version = match.group("ver")
release = match.group("rel")
print("Version:", version, "-- Release:", release)


#---------------------------------------------------------------------------
# Mock libraries that are not available on Read the Docs

on_read_the_docs = (os.environ.get("READTHEDOCS", None) == "True")
if on_read_the_docs:
    from mock import MagicMock
    class Mock(MagicMock):
        @classmethod
        def __getattr__(cls, name):
            return Mock()
    mock_modules = ["ctypes", "ctypes.wintypes", "pythoncom",
                    "pywintypes", "win32api", "win32clipboard",
                    "win32com", "win32com.client",
                    "win32com.client.gencache", "win32com.gen_py", 
                    "win32com.shell", "win32con", "win32event",
                    "win32file", "win32gui", "winsound", "winxpgui"]
    for module_name in mock_modules:
        sys.modules[module_name] = Mock()


#---------------------------------------------------------------------------
# General configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]
templates_path = ["templates"]
source_suffix = ".txt"
master_doc = "index"

project = u"Dragonfly"
copyright = u"2014, Christo Butcher"

today_fmt = "%Y-%m-%d"
exclude_trees = []
add_module_names = False
pygments_style = "sphinx"
autoclass_content = "both"


#---------------------------------------------------------------------------
# Options for HTML output

html_theme = "default"
html_last_updated_fmt = "%Y-%m-%d"
html_copy_source = True
htmlhelp_basename = "Dragonflydoc"


#---------------------------------------------------------------------------
# Options for LaTeX output

latex_documents = [
  ("index", "Dragonfly.tex", u"Dragonfly Documentation",
   u"Christo Butcher", "manual"),
]

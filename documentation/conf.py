# -*- coding: utf-8 -*-
#

import sys
import os
import os.path
import re

directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, directory)

#---------------------------------------------------------------------------
# Set an environment variable so that dragonfly can check if a sphinx build
# is running.

os.environ["SPHINX_BUILD_RUNNING"] = "1"


#---------------------------------------------------------------------------
# Gather version from distribution file.

path = os.path.join(directory, "version.txt")
version_string = open(path).readline()
match = re.match(r"\s*(?P<rel>(?P<ver>\d+\.\d+)(?:\.\S+)*)\s*", version_string)
version = match.group("ver")
release = match.group("rel")
print("Version:", version, "-- Release:", release)


#---------------------------------------------------------------------------
# Mock libraries that are only available on some platforms or with optional
# dependencies installed.

from mock import MagicMock

class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


mock_modules = {
    # Modules required on Windows
    "ctypes.wintypes",
    "pythoncom",
    "pywintypes",
    "win32api",
    "win32clipboard",
    "win32com",
    "win32com.client",
    "win32com.client.gencache",
    "win32com.gen_py",
    "win32com.shell",
    "win32con",
    "win32event",
    "win32file",
    "win32gui",
    "winsound",
    "winxpgui",

    # Modules required on Linux
    "psutil",

    # Modules required on macOS
    "AppKit",
    "applescript",

    # Modules required by dragonfly.rpc
    "decorator",
    "jsonrpc",
    "jsonrpc.dispatcher",
    "jsonrpc.manager",
    "werkzeug",
    "werkzeug.serving",
    "werkzeug.wrappers",

    # Modules required by Kaldi engine
    "kaldi_active_grammar",
    "sounddevice",
    "webrtcvad",

    # Modules required by Sphinx engine
    "jsgf",
    "jsgf.ext",
    "pocketsphinx",
    "pyaudio",
    "sphinxwrapper",

    # Other
    "ctypes",
    "numpy",
    "pyperclip",
    "regex",
}

for module_name in mock_modules:
    sys.modules[module_name] = Mock()


#---------------------------------------------------------------------------
# General configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinxarg.ext"]
templates_path = ["templates"]
source_suffix = ".txt"
master_doc = "index"

project = u"Dragonfly"
copyright = u"2014, Christo Butcher"

today_fmt = "%Y-%m-%d"
exclude_patterns = ["requirements.txt"]
add_module_names = False
pygments_style = "sphinx"
autoclass_content = "both"


#---------------------------------------------------------------------------
# Options for HTML output

html_theme = "sphinx_rtd_theme"
html_last_updated_fmt = "%Y-%m-%d"
html_copy_source = True
htmlhelp_basename = "Dragonflydoc"


#---------------------------------------------------------------------------
# Options for LaTeX output

latex_documents = [
  ("index", "Dragonfly.tex", u"Dragonfly Documentation",
   u"Christo Butcher", "manual"),
]

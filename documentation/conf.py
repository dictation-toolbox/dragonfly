# -*- coding: utf-8 -*-
#

import ctypes
import sys
import os
import os.path
import re


#---------------------------------------------------------------------------
# Put the root directory of the repository onto the module search path so
#  that dragonfly may be imported.
directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, directory)


#---------------------------------------------------------------------------
# Enable logging if building with Python version 2.7.
if sys.version_info.major == 2:
    import logging
    logging.basicConfig()


#---------------------------------------------------------------------------
# Set an environment variable so that dragonfly can check if a sphinx build
# is running.

os.environ["SPHINX_DOC_BUILD"] = "1"


#---------------------------------------------------------------------------
# Gather version from distribution file.

path = os.path.join(directory, "version.txt")
version_string = open(path).readline()
match = re.match(r"\s*(?P<rel>(?P<ver>\d+\.\d+)(?:\.\S+)*)\s*", version_string)
version = match.group("ver")
release = match.group("rel")
print("Version:", version, "-- Release:", release)


#---------------------------------------------------------------------------
# Mock Python modules that are only available on some platforms or if
#  optional dependencies are installed.

from mock import MagicMock

class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


# Define modules that should always be mocked prior to building the
#  documentation.
mock_modules = {
    # Modules required by Kaldi engine.
    "kaldi_active_grammar",
    "sounddevice",
    "webrtcvad",

    # Modules required by Sphinx engine.
    "jsgf",
    "jsgf.ext",
    "pocketsphinx",
    "sounddevice",
    "sphinxwrapper",

    # Other.
    "numpy",
    "psutil",
    "pynput",
    "pynput.keyboard",
    "pynput.mouse",
    "pyperclip",
    "regex",
}


# If this is not Windows, include modules required when running on that
#  platform.
if sys.platform != "win32":
    mock_modules.update({ "ctypes.wintypes", "natlink" })

    # Mock Windows-specific symbols from ctypes.
    ctypes.windll = Mock()
    ctypes.WinError = Mock()
    ctypes.WINFUNCTYPE = Mock()


# Include pywin32 modules, if necessary.
try:
    import win32api
except:
    mock_modules.update({
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
        "win32process",
        "winsound",
        "winxpgui",
    })

# If this is not macOS, include modules required when running on that
#  platform.
if sys.platform != "darwin":
    mock_modules.update({ "AppKit", "applescript" })

# Finally, mock the necessary Python modules.
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

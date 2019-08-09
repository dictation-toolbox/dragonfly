#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it 
#   under the terms of the GNU Lesser General Public License as published 
#   by the Free Software Foundation, either version 3 of the License, or 
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but 
#   WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public 
#   License along with Dragonfly.  If not, see 
#   <http://www.gnu.org/licenses/>.
#

import os.path
import re
from setuptools import setup, find_packages


#---------------------------------------------------------------------------
# Gather version from distribution file.

directory = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(directory, "version.txt")
version_string = open(path).readline()
match = re.match(r"\s*(?P<rel>(?P<ver>\d+\.\d+)(?:\.\S+)*)\s*", version_string)
version = match.group("ver")
release = match.group("rel")


#---------------------------------------------------------------------------
# Set up package.

def read(*names):
    return open(os.path.join(os.path.dirname(__file__), *names)).read()


setup(
      name             = "dragonfly2",
      version          = release,
      description      = "Speech recognition extension library",
      author           = "Christo Butcher",
      author_email     = "dist.dragonfly@twizzy.biz",
      maintainer       = "Dane Finlay",
      maintainer_email = "Danesprite@posteo.net",
      license          = "LICENSE.txt",
      url              = "https://github.com/dictation-toolbox/dragonfly",
      zip_safe         = False,  # To unzip documentation files.
      long_description = read("README.rst"),

      package_data={
                    "": ["*.txt", "*.rst"]
                   },

      install_requires=[
                        "setuptools >= 0.6c7",
                        "six",
                        "pyperclip >= 1.7.0",
                        "enum34;python_version<'3.4'",
                        "regex",
                        "decorator",

                        # Windows-only dependencies.
                        "comtypes;platform_system=='Windows'",
                        "pywin32;platform_system=='Windows'",

                        # Linux dependencies.
                        # "python-libxdo;platform_system=='Linux'",
                        # "Xlib;platform_system=='Linux'",
                        "psutil >= 5.5.1;platform_system=='Linux'",

                        # Mac OS dependencies.
                        "pynput >= 1.4.2;platform_system=='Darwin'",

                        # RPC requirements
                        "json-rpc",
                        "Werkzeug",
                        "requests",
                       ],

      extras_require={
          "sphinx": [
                     "sphinxwrapper >= 1.2.0",
                     "pyjsgf >= 1.7.0",
                     "pyaudio"
                    ],
          "kaldi": [
                    "kaldi-active-grammar ~= 0.6.0",
                    "pyaudio == 0.2.*",
                    "webrtcvad == 2.0.*",
                   ],
      },

      classifiers=[
                   "Environment :: Win32 (MS Windows)",
                   "Development Status :: 4 - Beta",
                   "License :: OSI Approved :: "
                   "GNU Library or Lesser General Public License (LGPL)",
                   "Operating System :: Microsoft :: Windows",
                   "Programming Language :: Python",
                  ],

      packages=find_packages(),

      test_suite="dragonfly.test.suites.text_suite",
     )

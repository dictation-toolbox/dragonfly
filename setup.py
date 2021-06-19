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
from setuptools import setup, find_packages, Command


#---------------------------------------------------------------------------
# Gather version from distribution file.

directory = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(directory, "version.txt")
version_string = open(path).readline()
match = re.match(r"\s*(?P<rel>(?P<ver>\d+\.\d+)(?:\.\S+)*)\s*", version_string)
version = match.group("ver")
release = match.group("rel")

#---------------------------------------------------------------------------
# Override the 'test' command to use pytest instead.
# Test requirements are located in the 'test_requirements.txt' file.

class test(Command):
    description = 'run unit tests and doctests after in-place build'
    user_options = [
        # (long option, short option, description)
        # '=' means an argument should be supplied.
        ('test-suite=', None, 'Dragonfly engine to test (default: "text")'),
        ('pytest-options=', 'o',
            'pytest options (ex: "-s" to expose stdout/stdin)'),
    ]

    def initialize_options(self):
        self.test_suite = 'text'
        self.pytest_options = ''

    def finalize_options(self):
        # Check that 'test_suite' is an engine name.
        from dragonfly.test.suites import engine_tests_dict
        suite = self.test_suite
        assert suite in engine_tests_dict.keys(), \
            "the test suite value must be an engine name, not '%s'" % suite

        # Split pytest options into a list.
        self.pytest_options = self.pytest_options.split()

    def run(self):
        from dragonfly.test.suites import run_pytest_suite
        print("Test suite running for engine '%s'" % self.test_suite)
        result = run_pytest_suite(self.test_suite, self.pytest_options)

        # Exit using pytest's return code.
        exit(int(result))


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
      include_package_data=True,
      install_requires=[
                        "setuptools >= 40.0.0",
                        "packaging >= 19.0",
                        "six",
                        "pyperclip >= 1.7.0",
                        "enum34;python_version<'3.4'",
                        "regex",
                        "decorator",
                        "lark-parser == 0.8.*",

                        # Windows-only dependencies.
                        "comtypes;platform_system=='Windows'",
                        "pywin32;platform_system=='Windows'",

                        # Linux dependencies.
                        # "python-libxdo;platform_system=='Linux'",
                        # "Xlib;platform_system=='Linux'",
                        "psutil >= 5.5.1;platform_system=='Linux'",
                        "pynput >= 1.4.2;platform_system=='Linux'",

                        # Mac OS dependencies.
                        "pynput >= 1.4.2;platform_system=='Darwin'",
                        "pyobjc >= 5.2;platform_system=='Darwin'",
                        "py-applescript == 1.0.0;platform_system=='Darwin'",

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
                    "kaldi-active-grammar ~= 2.1.0",
                    "sounddevice == 0.3.*",
                    "webrtcvad-wheels == 2.0.*",
                   ],
      },

      cmdclass={
          "test": test,
      },

      classifiers=[
                   "Development Status :: 4 - Beta",
                   "Environment :: Win32 (MS Windows)",
                   "Environment :: X11 Applications",
                   "Environment :: MacOS X",
                   "License :: OSI Approved :: "
                   "GNU Library or Lesser General Public License (LGPL)",
                   "Intended Audience :: Developers",
                   "Operating System :: Microsoft :: Windows",
                   "Operating System :: POSIX",
                   "Operating System :: MacOS",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3.4",
                   "Programming Language :: Python :: 3.5",
                   "Programming Language :: Python :: 3.6",
                   "Programming Language :: Python :: 3.7",
                   "Programming Language :: Python :: Implementation :: CPython",
                   "Topic :: Multimedia :: Sound/Audio :: Speech",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                  ],

      packages=find_packages(),

      test_suite="dragonfly.test.suites.text_suite",
     )

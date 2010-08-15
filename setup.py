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

from ez_setup import use_setuptools
use_setuptools()

import os.path
import re
import sys
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
# Prepare Google code uploader.

try:
    from googlecode_distutils_upload import upload as upload_gcode
except ImportError:
    import distutils.core
    class upload_gcode(distutils.core.Command):
        user_options = []
        def __init__(self, *args, **kwargs):
            sys.stderr.write("error: Install this module in"
                             " site-packages to upload:"
                             " http://support.googlecode.com/svn/"
                             "trunk/scripts/googlecode_distutils"
                             "_uload.py")
            sys.exit(3)


#---------------------------------------------------------------------------
# Set up package.

def read(*names):
    return open(os.path.join(os.path.dirname(__file__), *names)).read()

setup(
      name          = "dragonfly",
      version       = release,
      description   = "Speech recognition extension library",
      author        = "Christo Butcher",
      author_email  = "dist.dragonfly@twizzy.biz",
      license       = "LGPL",
      url           = "http://code.google.com/p/dragonfly/",
      zip_safe      = False,  # To unzip documentation files.
      long_description = read("README.txt"),

      install_requires = "setuptools >= 0.6c7",

      classifiers=[
                   "Environment :: Win32 (MS Windows)",
                   "Development Status :: 4 - Beta",
                   "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
                   "Operating System :: Microsoft :: Windows",
                   "Programming Language :: Python",
                  ],

      packages=find_packages(),

      test_suite="dragonfly.test.suite_natlink",

      cmdclass={'upload_gcode': upload_gcode},
     )

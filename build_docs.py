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

"""
Documentation build script
============================================================================

"""

import sys
import os
import subprocess


#===========================================================================

build_binary = r"c:\python26\scripts\sphinx-build-script.py"
build_type = "html"

def run_sphinx():
    python_binary = sys.executable
    directory = os.path.dirname(__file__)
    src_dir = os.path.abspath(os.path.join(directory, "documentation"))
    dst_dir = os.path.abspath(os.path.join(directory, "build", "documentation"))

    arguments = [python_binary, build_binary,
                 "-a", "-b",
                 build_type, src_dir, dst_dir]
    subprocess.call(arguments)


#===========================================================================

if __name__ == "__main__":
    run_sphinx()

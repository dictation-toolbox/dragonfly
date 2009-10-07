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
This script installs a development link to the Dragonfly 
source directory into the local Python distribution.

This is useful for Dragonfly developers, because it lets 
them have a working copy checked out from the Dragonfly 
repository somewhere, and at the same time have that copy 
directly accessible through ``import dragonfly``.

"""


import sys
import os
import os.path
import subprocess


def main():
    from pkg_resources import resource_filename
    setup_path = os.path.abspath(resource_filename(__name__, "setup.py"))

    commands = ["egg_info", "--tag-build=.dev", "-r", "develop"]

    arguments = [sys.executable, setup_path] + commands
    os.chdir(os.path.dirname(setup_path))
    subprocess.call(arguments)
 

if __name__ == "__main__":
    main()

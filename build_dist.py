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


import sys
import os
import os.path
import subprocess

upload = False

from pkg_resources import resource_filename
setup_path = os.path.abspath(resource_filename(__name__, "setup.py"))

commands = []
commands += ["egg_info", "--tag-build=.dev", "-r"]
commands += ["sdist"]
commands += ["bdist_wininst"]
#commands += ["bdist_msi"]
commands += ["bdist_egg"]

if upload:
    # Make sure HOME is defined; required for .pypirc use.
    if "HOME" not in os.environ:
        os.putenv("HOME", os.path.expanduser("~"))
    commands.insert(3, "register")
    commands += ["upload", "--show-response"]
#    commands += ["upload_gcode", "--src"]
#    commands += ["upload_gcode", "--windows"]

arguments = [sys.executable, setup_path] + commands
os.chdir(os.path.dirname(setup_path))
subprocess.call(arguments)

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
from pkg_resources import resource_filename
import googlecode_upload


#---------------------------------------------------------------------------
# Functions for running setup.py and building packages.

def build_commands(commands, directory, setup_path):
    # Make sure HOME is defined; required for .pypirc use
    if "HOME" not in os.environ:
        os.putenv("HOME", os.path.expanduser("~"))

    arguments = [sys.executable, setup_path] + commands
    os.chdir(directory)
    subprocess.call(arguments)


def build_distribution_and_upload(directory, setup_path):
    # Register and upload to pypi.
    commands = [
                "egg_info", "--tag-build=.dev", "-r",
                "register",
                "sdist",
                "bdist_wininst",
                "bdist_egg",
                "upload", "--show-response",
               ]
    build_commands(commands, directory, setup_path)

    # Find new packages to upload to Google code.
    dist_directory = os.path.join(directory, "dist")
    filelist = []
    for filename in os.listdir(dist_directory):
        path = os.path.join(dist_directory, filename)
        modified = os.path.getmtime(path)
        filelist.append((modified, path))
    filelist = sorted(filelist)
    most_recent_path = filelist[-1][1]
    print "most recent", most_recent_path
    filename = os.path.basename(most_recent_path)
    basename, extension = os.path.splitext(filename)
    print "most recent basename", basename
    if extension != ".egg":
        raise RuntimeError("Most recent package not an egg file: %r"
                           % most_recent_path)
    if not basename.startswith("dragonfly-"):
        raise RuntimeError("Most recent package not for dragonfly: %r"
                           % most_recent_path)
    if basename[-6:-3] != "-py":
        raise RuntimeError("Most recent package funny name: %r"
                           % most_recent_path)
    basename = basename[:-6]

    # Upload to Google code.
    upload_gcode(directory, basename)


def build_distribution(directory, setup_path):
    commands = [
                "egg_info", "--tag-build=.dev", "-r",
                "sdist",
                "bdist_wininst",
                "bdist_egg",
               ]
    build_commands(commands, directory, setup_path)


#---------------------------------------------------------------------------
# Functions for uploading to Google code.

def load_gcode_credentials(path):
    namespace = {}
    exec open(path, "r").read() in namespace
    return namespace["gcode_username"], namespace["gcode_password"]


def upload_gcode_single(path, summary, labels, username, password):
    googlecode_upload.upload(
                             file=path,
                             project_name="dragonfly",
                             user_name=username,
                             password=password,
                             summary=summary,
                             labels=labels,
                            )


def upload_gcode(directory, basename):
    credentials_path = os.path.join(directory, "local.txt")
    basepath = os.path.join(directory, "dist", basename)
    basepath = basepath.replace("_", "-")
    username, password = load_gcode_credentials(credentials_path)
    upload_gcode_single(
                        basepath + ".win32.exe",
                        "Windows installer",
                        ["Featured", "OpSys-Windows", "Type-Installer"],
                        username, password,
                       )
    upload_gcode_single(
                        basepath + ".zip",
                        "Source archive",
                        ["Featured", "OpSys-Windows", "Type-Source"],
                        username, password,
                       )


#---------------------------------------------------------------------------
# Main control.

def main():
    # Retrieve directory and file location information.
    setup_path = os.path.abspath(resource_filename(__name__, "setup.py"))
    directory = os.path.dirname(setup_path)

    # Build the distribution packages.
    build_distribution(directory, setup_path)


if __name__ == "__main__":
    main()

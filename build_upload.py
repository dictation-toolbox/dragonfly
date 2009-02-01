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
from pkg_resources import resource_filename

from build_dist import build_distribution_and_upload



#---------------------------------------------------------------------------
# Main control.

def main():
    # Retrieve directory and file location information.
    setup_path = os.path.abspath(resource_filename(__name__, "setup.py"))
    directory = os.path.dirname(setup_path)

    # Build and upload the distribution packages.
    build_distribution_and_upload(directory, setup_path)


if __name__ == "__main__":
    main()

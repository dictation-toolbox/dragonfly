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
"""


import sys
import os.path
import subprocess


#===========================================================================

def run_nose():
    import nose.core
    import coverage.control
    from pkg_resources import resource_filename

    # Determine directory in which to save coverage report.
    setup_path = os.path.abspath(resource_filename(__name__, "setup.py"))
    directory = os.path.dirname(setup_path)
    cover_dir = os.path.join(directory, "coverage")

    # Virtual commandline arguments to be given to nose.
    argv = [
            sys.argv[0],
            "--failure-detail",
            "--with-doctest",
            "--doctest-extension=doctest",
           ]

    # Clear coverage history and start new coverage measurement.
    coverage = coverage.control.coverage()
    coverage.erase()
    coverage.start()

    # Let nose run tests.
    nose.core.TestProgram(argv=argv, exit=False)

    # Save coverage data and generate HTML report.
    coverage.stop()
    coverage.save()
    coverage.html_report(directory=cover_dir)


def run_pylint():
    from pylint import lint
    args = [
            "dragonfly",
           ]
    lint.Run(args)


def run_pep8():
    import pep8
    argv = [
            sys.argv[0],
            "--filename=*.py",
           ]
    from pkg_resources import resource_filename
    setup_path = os.path.abspath(resource_filename(__name__, "setup.py"))
    directory = os.path.dirname(setup_path)
    pep8.process_options(argv)
    pep8.input_dir(directory)


#===========================================================================

def main():
#    run_pep8()
#    run_pylint()
    run_nose()

if __name__ == "__main__":
    main()

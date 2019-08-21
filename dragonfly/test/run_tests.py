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
Main test runner script
============================================================================

This file is Dragonfly's main test script.  Running it will execute all
tests within the Dragonfly library.


Dependencies
----------------------------------------------------------------------------

This script uses several external libraries to collect, run, and analyze
the Dragonfly tests.  It requires the following external dependencies:

 * `Nose <http://somethingaboutorange.com/mrl/projects/nose/>`_ --
   an extension on unittest.
 * `Coverage <http://nedbatchelder.com/code/coverage/>`_ --
   a code coverage measuring tool.

"""

import sys
import os.path
import subprocess


#===========================================================================
# Test control functions for the various types of tests: nose, pep8, pylint.

def run_nose():
    """ Use Nose to collect and execute test cases within Dragonfly. """
    import nose.core
#    import coverage.control
    from pkg_resources import resource_filename

    # Determine directory in which to save coverage report.
    setup_path = os.path.abspath(resource_filename("dragonfly", "license.txt"))
    directory = os.path.dirname(os.path.dirname(setup_path))
    cover_dir = os.path.join(directory, "coverage")

    # Virtual commandline arguments to be given to nose.
    argv = [
            sys.argv[0],
            "--failure-detail",
#            "--with-doctest",
#            "--doctest-extension=doctest",
            directory,
           ]

    # Clear coverage history and start new coverage measurement.
#    coverage = coverage.control.coverage()
#    coverage.erase()
#    coverage.start()

    # Let nose run tests.
    nose.core.TestProgram(argv=argv, exit=False)

    # Save coverage data and generate HTML report.
#    coverage.stop()
#    coverage.save()
#    coverage.html_report(directory=cover_dir)


def run_pylint():
    """ Use the pylint package to analyze the Dragonfly source code. """
    from pylint import lint
    args = [
            "dragonfly",
           ]
    lint.Run(args)


def run_pep8():
    """ Use the pep8 package to analyze the Dragonfly source code. """
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
# This script's main control logic.

def main():
    from dragonfly.log import setup_tracing
    setup_tracing(sys.stdout, limit=30)
#    run_pep8()
#    run_pylint()
    run_nose()


if __name__ == "__main__":
    main()

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

from cgitb import reset
import os.path
import re
from setuptools import setup, find_packages, Command

def main():

    description = 'run unit tests and doctests after in-place build'
    user_options = [
        # (long option, short option, description)
        # '=' means an argument should be supplied.
        ('test-suite=', None, 'Dragonfly engine to test (default: "text")'),
        ('pytest-options=', 'o',
            'pytest options (ex: "-s" to expose stdout/stdin)'),
    ]

    test_suite = 'text'
    pytest_options = ''

    # Check that 'test_suite' is an engine name.
    from dragonfly.test.suites import engine_tests_dict
    suite =test_suite
    assert suite in engine_tests_dict.keys(), \
        "the test suite value must be an engine name, not '%s'" % suite

    # Split pytest options into a list.
    pytest_options = pytest_options.split()

    from dragonfly.test.suites import run_pytest_suite
    print("Test suite running for engine '%s'" % test_suite)
    result = run_pytest_suite(test_suite, pytest_options)

    # Exit using pytest's return code.
    return result

if __name__ =="__main__":
    result=main()
    exit(int(result))
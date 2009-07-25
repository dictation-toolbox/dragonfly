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
Test script for the Dragonfly library
============================================================================

"""

import unittest
import doctest


#---------------------------------------------------------------------------
# Create the central test suite containing all tests.

suite = unittest.TestSuite()


#---------------------------------------------------------------------------
# Add doctest'd modules to the test suite.

doctest_modules = [
                   "dragonfly.parser",
                   "dragonfly.apps.family.loader_parser",
                  ]

for module_path in doctest_modules:
    suite.addTest(doctest.DocTestSuite(module_path))


#---------------------------------------------------------------------------
# If this file is run as a script, execute the central test suite.

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)

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

import unittest
import doctest
import pkg_resources
import os.path
from dragonfly.test.engine_suite import EngineTestSuite


#===========================================================================

common_names   = [
                  ".test_language_en_number",
                  ".test_language_de_number",
                  ".test_language_nl_number",
                  ".test_engine_nonexistent",
                  "doc:documentation/recobs_doctest.txt",
                 ]

natlink_names  = [
                  ".test_engine_natlink",
                 ]

sapi5_names    = [
                  ".test_engine_sapi5",
                 ]

#===========================================================================

def build_suite(suite, names):
    # Determine the root directory of the source code files.  This is
    #  used for finding doctest files specified relative to that root.
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    project_root = os.path.abspath(project_root)

    # Load test cases from specified names.
    loader = unittest.defaultTestLoader
    for name in names:
        if name.startswith("."):
            name = "dragonfly.test" + name
            suite.addTests(loader.loadTestsFromName(name))
        elif name.startswith("doc:"):
            path = name[4:]
            path = os.path.join(project_root, *path.split("/"))
            path = os.path.abspath(path)
            suite.addTests(doctest.DocFileSuite(path))
        else:
            raise Exception("Invalid test name: %r." % (name,))
    return suite


natlink_suite  = build_suite(EngineTestSuite("natlink"),
                             common_names + natlink_names)
sapi5_suite    = build_suite(EngineTestSuite("sapi5"),
                             common_names + sapi5_names)

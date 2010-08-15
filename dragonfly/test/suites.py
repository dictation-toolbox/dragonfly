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
from dragonfly.test.engine_suite import EngineTestSuite


#===========================================================================

common_names   = [
                  ".test_language_en_number",
                  ".test_language_de_number",
                  ".test_language_nl_number",
                  ".test_engine_nonexistent",
                 ]

natlink_names  = [
                  ".test_engine_natlink",
                 ]

sapi5_names    = [
                  ".test_engine_sapi5",
                 ]

#===========================================================================

def build_suite(suite, names):
    loader = unittest.defaultTestLoader
    for name in names:
        if name.startswith("."):
            name = "dragonfly.test" + name
        suite.addTests(loader.loadTestsFromName(name))
    return suite


natlink_suite  = build_suite(EngineTestSuite("natlink"),
                             common_names + natlink_names)
sapi5_suite    = build_suite(EngineTestSuite("sapi5"),
                             common_names + sapi5_names)

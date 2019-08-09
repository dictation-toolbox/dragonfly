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
import dragonfly


#===========================================================================

class EngineTestSuite(unittest.TestSuite):

    def __init__(self, name):
        self.engine_name = name
        unittest.TestSuite.__init__(self)

    def run(self, result):
        self.engine = dragonfly.get_engine(self.engine_name)
        self.engine.connect()

        # Prevent the engine from running timers on its own. This lets us
        # avoid race conditions.
        self.engine._timer_manager.disable()

        try:
            return unittest.TestSuite.run(self, result)
        finally:
            self.engine.disconnect()

    def tearDownClass(cls):
        # Check that the dragonfly engine was not changed during the tests.
        assert cls.engine is dragonfly.get_engine()

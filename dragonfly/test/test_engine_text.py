#
# This file is part of Dragonfly.
# (c) Copyright 2018 by Dane Finlay
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
from dragonfly.engines import get_engine, EngineBase, EngineError


#---------------------------------------------------------------------------

class TestEngineText(unittest.TestCase):

    def test_get_engine_text_is_usable(self):
        """ Verify that the text engine is usable. """
        engine = get_engine("text")
        assert isinstance(engine, EngineBase)
        assert engine.name == "text"
        engine.connect()
        try:
            from dragonfly import Literal
            from dragonfly.test import ElementTester
            tester = ElementTester(Literal("hello world"))
            results = tester.recognize("hello world")
            assert results == "hello world"
        finally:
            engine.disconnect()

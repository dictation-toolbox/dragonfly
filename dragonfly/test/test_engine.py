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
Test cases for the main engine interface
============================================================================

"""

import unittest
from dragonfly.engines import get_engine, EngineBase, EngineError


#---------------------------------------------------------------------------

class TestEngines(unittest.TestCase):
    """ Main engine interface tests. """

    def test_get_engine_nonexistent(self):
        engine = get_engine("nonexistent")

    def test_get_engine_automatic(self):
        """ Verify that an engine can be selected automatically. """
        engine = get_engine()
        assert isinstance(engine, EngineBase)

    def test_get_engine_automatic_is_usable(self):
        """ Verify that the automatically selected engine is usable. """
        engine = get_engine()
        engine.connect()
        try:
            engine.speak("testing automatic")
            from dragonfly import Literal
            from dragonfly.test import ElementTester
            tester = ElementTester(Literal("hello world"))
            results = tester.recognize("hello world")
            assert results == "hello world"
        finally:
            engine.disconnect()

    def test_get_engine_natlink_is_usable(self):
        """ Verify that the natlink engine is usable. """
        engine = get_engine("natlink")
        assert isinstance(engine, EngineBase)
        assert engine.name == "natlink"
        engine.connect()
        try:
            engine.speak("testing natlink")
            from dragonfly import Literal
            from dragonfly.test import ElementTester
            tester = ElementTester(Literal("hello world"))
            results = tester.recognize("hello world")
            assert results == "hello world"
        finally:
            engine.disconnect()

    def test_get_engine_sapi5_is_usable(self):
        """ Verify that the sapi5 engine is usable. """
        engine = get_engine("sapi5")
        assert isinstance(engine, EngineBase)
        assert engine.name == "sapi5"
        engine.connect()
        try:
            engine.speak("testing WSR")
            from dragonfly import Literal
            from dragonfly.test import ElementTester
            tester = ElementTester(Literal("hello world"), engine=engine)
            results = tester.recognize("hello world")
            assert results == "hello world", "%r != %r" % (results, "hello world")
        finally:
            engine.disconnect()

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
import sys

from dragonfly import (ActionBase, CompoundRule, Grammar, Literal,
                       MappingRule, Rule, get_engine)
from dragonfly.rpc import RPCServer


class RPCTestCase(unittest.TestCase):
    """
    Tests for RPC server methods.
    """

    @classmethod
    def setUpClass(cls):
        cls.server = RPCServer()
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_add_method(self):
        """ Verify that RPC methods can be added and replaced."""
        self.server.add_method("foo", lambda: "bar")
        response = self.server.send_request("foo", [])
        self.assertEqual(response, {'jsonrpc': '2.0', 'result': 'bar',
                                    'id': 0})
        self.server.add_method("foo", lambda: "foo")
        response = self.server.send_request("foo", [])
        self.assertEqual(response, {'jsonrpc': '2.0', 'result': 'foo',
                                    'id': 0})

    def test_remove_method(self):
        """ Verify that RPC methods can be removed."""
        # The following should not raise an error.
        self.server.remove_method("non_existent")

        # Add a 'bar' method, check that it works.
        self.server.add_method("bar", lambda: "foo")
        response = self.server.send_request("bar", [])
        self.assertEqual(response, {'jsonrpc': '2.0', 'result': 'foo',
                                    'id': 0})

        # Remove it and check that an error is returned by the server.
        # 'send_request' will raise a RuntimeError if the server returns an
        # error.
        self.server.remove_method("bar")
        self.assertRaises(RuntimeError,
                          lambda: self.server.send_request("bar", []))

    def test_list_grammars(self):
        # Load a Grammar with three rules and check that the RPC returns the
        # correct data for them.
        g = Grammar("list_grammars_test")
        g.add_rule(CompoundRule(name="compound", spec="testing",
                                exported=True))
        g.add_rule(MappingRule(name="mapping", mapping={
            "command a": ActionBase(),
            "command b": ActionBase()
        }))
        g.add_rule(Rule(name="base", element=Literal("hello world"),
                        exported=False))
        g.load()

        response = self.server.send_request("list_grammars", [])
        self.assertIn("result", response)
        expected_grammar_data = {
            "name": g.name, "enabled": True, "active": True, "rules": [
                {"name": "compound", "specs": ["testing"],
                 "exported": True, "active": True},
                {"name": "mapping", "specs": ["command a", "command b"],
                 "exported": True, "active": True},
                {"name": "base", "specs": ["hello world"],
                 "exported": False, "active": True}
            ]
        }
        # Check that the loaded grammar appears in the result. It might not
        # be the only grammar and that is acceptable because dragonfly's
        # tests can be run while user grammars are loaded.
        try:
            self.assertIn(expected_grammar_data, response["result"])
        finally:
            g.unload()


if __name__ == '__main__':
    # Use the "text" engine by default.
    get_engine("text")
    unittest.main()

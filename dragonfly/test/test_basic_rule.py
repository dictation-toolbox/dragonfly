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

from dragonfly import BasicRule, Repetition, Alternative, Literal, Function
from dragonfly.test import RuleTestCase


class TestBasicRule(RuleTestCase):

    def test_basic_rule(self):
        """ Verify that BasicRules can be loaded and recognized correctly.
        """
        test = []
        func = lambda x: test.append(x)

        # Test using BasicRule directly.
        rule = BasicRule(element=Repetition(
            Alternative((
                Literal("test one", value=Function(lambda: func(1))),
                Literal("test two", value=Function(lambda: func(2))),
                Literal("test three", value=Function(lambda: func(3))),
            )),
            1, 5
        ))
        self.add_rule(rule)
        self.recognize("test one test two test three".split())
        assert test == [1, 2, 3], "BasicRule was not processed correctly"

        # Remove the rule and clear the test list.
        self.grammar.remove_rule(rule)
        del test[:]

        # Test using a sub-class of BasicRule.
        class MyBasicRule(BasicRule):
            element = Repetition(
                Alternative((
                    Literal("test one", value=Function(lambda: func(1))),
                    Literal("test two", value=Function(lambda: func(2))),
                    Literal("test three", value=Function(lambda: func(3))),
                )),
                1, 5
            )
        self.add_rule(MyBasicRule())
        self.recognize("test one test two test three".split())
        assert test == [1, 2, 3], "BasicRule was not processed correctly"

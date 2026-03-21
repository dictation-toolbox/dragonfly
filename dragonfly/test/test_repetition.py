#
# This file is part of Dragonfly.
# Licensed under the LGPL.
#

import unittest

from dragonfly import Alternative, Literal, Repetition, get_engine
from dragonfly.test import ElementTester


class TestRepetition(unittest.TestCase):

    def setUp(self):
        self.engine = get_engine("text")

    def test_value_includes_single_optional_tail(self):
        tester = ElementTester(
            Repetition(
                Alternative((
                    Literal("alpha", value="A"),
                    Literal("beta", value="B"),
                )),
                min=1,
                max=2,
            ),
            engine=self.engine,
        )

        assert tester.recognize("alpha beta") == ["A", "B"]

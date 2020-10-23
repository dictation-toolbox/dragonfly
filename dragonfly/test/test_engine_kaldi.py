"""
Tests for the Kaldi engine

Most engine functionality is tested here, although the tests are done
entirely via `mimic`, so there are some things which have to be tested
manually.

These tests assume that the `kaldi_model` model is used.

Adapted from `test_engine_sphinx.py`.
"""

import unittest

import logging

from dragonfly.engines import (EngineBase, get_engine)
from dragonfly.grammar.elements import Literal, Sequence
from dragonfly.test import ElementTester

try:
    from dragonfly.engines.backend_kaldi.engine import KaldiError
except ImportError:
    KaldiError = Exception


class MockLoggingHandler(logging.Handler):
    """
    Mock logging handler to check for expected logs.
    Adapted this from a Stack Overflow answer: https://stackoverflow.com/a/1049375
    """

    def __init__(self, *args, **kwargs):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())


class KaldiEngineTests(unittest.TestCase):
    """
    Tests for the Kaldi engine.
    """
    def test_get_engine_kaldi_is_usable(self):
        """
        Verify that the kaldi engine is usable by testing that a simple
        rule is loaded correctly and works correctly.
        """
        engine = get_engine()
        assert engine.name == "kaldi"
        assert isinstance(engine, EngineBase)
        engine.speak("testing kaldi")

        # Test that a basic rule can be loaded and recognized.
        seq = Sequence([Literal("hello"), Literal("world")])
        tester = ElementTester(seq, engine=engine)
        results = tester.recognize("hello world")
        self.assertEqual(results, [u"hello", u"world"])

    # FIXME: handling reseting user lexicon
    # def test_unknown_grammar_words(self):
    #     """ Verify that warnings are logged for a grammar with unknown words. """
    #     grammar = Grammar("test")
    #     grammar.add_rule(CompoundRule(name="r1", spec="testing unknownword"))
    #     grammar.add_rule(CompoundRule(name="r2", spec="wordz|morwordz"))

    #     # Catch log messages.
    #     handler = MockLoggingHandler()
    #     log = logging.getLogger("engine.compiler")
    #     log.addHandler(handler)
    #     grammar.load()
    #     log.removeHandler(handler)

    #     # Check the logged messages.
    #     warnings = handler.messages["warning"]
    #     self.assertEqual(len(warnings), 3)
    #     self.assertIn("unknownword", warnings[0])
    #     self.assertIn("wordz", warnings[1])
    #     self.assertIn("morwordz", warnings[2])
    #     self.assertNotIn("testing", '\n'.join(warnings))


# ---------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()

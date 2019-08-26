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
"""

import logging
from six import string_types

from dragonfly              import *
from .error                 import TestError
from ..test                 import infrastructure


#===========================================================================

class RuleTestGrammar(Grammar):

    _log = logging.getLogger("test")
    _NoRecognition = infrastructure.Unique("NoRecognition")

    #-----------------------------------------------------------------------

    def __init__(self, name=None, engine=None, context=None):
        if name is None:
            name = self.__class__.__name__
        Grammar.__init__(self, name=name, engine=engine, context=context)

    def recognize(self, words):
        if isinstance(words, string_types):
            words = words.split()

        if not self.loaded:
            self._log.debug("Loading TesterGrammar.")
            self.load()
            unload_after_recognition = True
        else:
            unload_after_recognition = False

        try:
            # Make this grammar exclusive; this *probably* avoids other
            #  grammars from being active and receiving the mimicked
            #  recognition.
            try:
                self.set_exclusiveness(True)
            except Exception as e:
                msg = ("Exception during setting grammar as"
                       " exclusive: %s" % (e,))
                self._log.exception(msg)
                raise TestError(msg)

            # Mimic recognition.
            try:
                self.engine.mimic(words)
            except MimicFailure as e:
                msg = "Recognition failed. (Words: %s)" % (words,)
                self._log.error(msg)
                raise TestError(msg)
            except Exception as e:
                msg = ("Exception during recognition: %s" % (e,))
                self._log.exception(msg)
                raise TestError(msg)

        finally:
            if unload_after_recognition:
                try:
                    self.unload()
                except Exception as e:
                    # Log exception, but do not reraise it as that would
                    #  mask any earlier exception.
                    self._log.exception("Failed to unload grammar: %s"
                                        % (e,))

    def recognize_node(self, words):
        """
            Mimic recognition of the given words and return the
            root node of the recognized rule.

            The root node of the recognized rule is collected by
            patching the `process_recognition` methods of all
            loaded rules in this grammar with a custom function.
            Note that this patching prevents any of the rules'
            original recognition processing logic from being
            executed.

        """
        # Logic to patch rules with process recognition for testing.
        self._recognized_node = self._NoRecognition
        def test_process_recognition(node):
            self._recognized_node = node

        # Patch rules with process recognition method for testing.
        patched_rules = []
        for rule in self.rules:
            if hasattr(rule, "process_recognition"):
                original_method = rule.process_recognition
                rule.process_recognition = test_process_recognition
                patched_rules.append((rule, original_method))

        try:
            self.recognize(words)

            # If no node was collected, then none of the
            #  patch rules received the recognition.
            if self._recognized_node == self._NoRecognition:
                msg = "Recognition hijacked. (Words: %s)" % (words,)
                self._log.error(msg)
                raise TestError(msg)
            return self._recognized_node

        finally:
            # Restore original process recognition methods.
            for rule, original_method in patched_rules:
                rule.process_recognition = original_method


    def recognize_extras(self, words):
        """
            Mimic recognition of the given words and return the
            the extras parameter for the recognized rule.

            The extras parameter for the recognized rule is collected
            by patching the `_process_recognition` methods of all
            loaded rules in this grammar with a custom function.
            Note that this patching prevents any of the rules'
            original recognition processing logic from being
            executed.

        """
        # Logic to patch rules with process recognition for testing.
        self._recognized_node = self._NoRecognition
        self._recognized_extras = self._NoRecognition
        def test_process_recognition(node, extras):
            self._recognized_node = node
            self._recognized_extras = extras

        # Patch rules with process recognition method for testing.
        patched_rules = []
        for rule in self.rules:
            if hasattr(rule, "_process_recognition"):
                original_method = rule._process_recognition
                rule._process_recognition = test_process_recognition
                patched_rules.append((rule, original_method))

        try:
            self.recognize(words)

            # If no extras were collected, then none of the
            #  patch rules received the recognition.
            if self._recognized_extras == self._NoRecognition:
                msg = "Recognition hijacked. (Words: %s)" % (words,)
                self._log.error(msg)
                raise TestError(msg)
            return self._recognized_extras

        finally:
            # Restore original process recognition methods.
            for rule, original_method in patched_rules:
                rule._process_recognition = original_method

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
Tools for testing element classes
============================================================================

"""

import logging
from six import string_types

from dragonfly              import *
from ..test                 import TestError, RecognitionFailure
from ..test.infrastructure  import Unique


#===========================================================================

class ElementTester(Grammar):

    _log = logging.getLogger("test.element")
    _NotSet = Unique("NoRecognition")

    class _ElementTestRule(Rule):
        exported = True
        def process_recognition(self, node):
            self.grammar._process_recognition(node)

    #-----------------------------------------------------------------------

    def __init__(self, element, engine=None):
        Grammar.__init__(self, self.__class__.__name__, engine=engine)
        rule = self._ElementTestRule("rule", element)
        self.add_rule(rule)

    def recognize(self, words):
        if isinstance(words, string_types):
            words = words.split()

        if not self.loaded:
            self._log.debug("Loading ElementTester instance.")
            self.load()
            unload_after_recognition = True
        else:
            unload_after_recognition = False

        self._recognized_value = self._NotSet
        try:
            # Make this grammar exclusive; this *probably* avoids other
            #  grammars from being active and receiving the mimicked
            #  recognition.
            self.set_exclusiveness(True)

            # Mimic recognition.
            try:
                self.engine.mimic(words)
            except MimicFailure as e:
                self._recognized_value = RecognitionFailure
            except Exception as e:
                self._log.exception("Exception within recognition: %s" % (e,))
                raise

        except Exception as e:
            self._log.exception("Exception during recognition: %s" % (e,))
            raise
        finally:
            if unload_after_recognition:
                try:
                    self.unload()
                except Exception as e:
                    raise TestError("Failed to unload grammar: %s" % e)

        # If recognition was successful but this grammar did not
        #  receive the recognition callback, then apparently some other
        #  grammar hijacked it; raise a TestError to signal this
        #  undesired situation.
        if self._recognized_value == self._NotSet:
            self._log.error(u"Recognition hijacked. (Words: %s)" % (words,))
            raise TestError(u"Recognition hijacked. (Words: %s)" % (words,))

        # Return the value of the element after recognition.
        return self._recognized_value

    def _process_recognition(self, node):
        element_node = node.children[0]
        self._recognized_value = element_node.value()

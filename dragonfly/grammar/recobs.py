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
Recognition observer classes
============================================================================

"""

import time
import logging

from six import integer_types

from ..actions.actions  import Playback
from ..engines          import get_engine


#---------------------------------------------------------------------------

class RecognitionObserver(object):
    """
    Recognition observer base class.

    Sub-classes should override one or more of the event methods.
    """

    _log = logging.getLogger("grammar")

    def __init__(self):
        pass

    def __del__(self):
        try:
            self.unregister()
        except Exception:
            pass

    def register(self):
        """
        Register the observer for recognition state events.
        """
        engine = get_engine()
        engine.register_recognition_observer(self)

    def unregister(self):
        """
        Unregister the observer for recognition state events.
        """
        engine = get_engine()
        engine.unregister_recognition_observer(self)

    def on_begin(self):
        """
        Method called when the observer is registered and speech start is
        detected.
        """

    def on_recognition(self, words, rule, node, results):
        """
        Method called when speech successfully decoded to a grammar rule or
        to dictation.

        This is called *before* grammar rule processing (i.e.
        ``Rule.process_recognition()``).

        :param words: recognized words
        :type words: tuple
        :param rule: *optional* recognized rule
        :type rule: Rule
        :param node: *optional* parse tree node
        :type node: Node
        :param results: *optional* engine recognition results object
        :type results: :ref:`engine-specific type<RefGrammarCallbackResultsTypes>`
        """

    def on_failure(self, results):
        """
        Method called when speech failed to decode to a grammar rule or to
        dictation.

        :param results: *optional* engine recognition results object
        :type results: :ref:`engine-specific type<RefGrammarCallbackResultsTypes>`
        """

    def on_end(self, results):
        """
        Method called when speech ends, either with a successful
        recognition (after ``on_recognition``) or in failure (after
        ``on_failure``).

        :param results: *optional* engine recognition results object
        :type results: :ref:`engine-specific type<RefGrammarCallbackResultsTypes>`
        """

    def on_post_recognition(self, words, rule, node, results):
        """
        Method called when speech successfully decoded to a grammar rule or
        to dictation.

        This is called *after* grammar rule processing (i.e.
        ``Rule.process_recognition()``).

        :param words: recognized words
        :type words: tuple
        :param rule: *optional* recognized rule
        :type rule: Rule
        :param node: *optional* parse tree node
        :type node: Node
        :param results: *optional* engine recognition results object
        :type results: :ref:`engine-specific type<RefGrammarCallbackResultsTypes>`
        """


#---------------------------------------------------------------------------

class RecognitionHistory(list, RecognitionObserver):
    """
        Storage class for recent recognitions.

        Instances of this class monitor recognitions and store them
        internally.  This class derives from the built in *list* type
        and can be accessed as if it were a normal *list* containing
        recent recognitions.  Note that an instance's contents are
        updated automatically as recognitions are received.

    """

    def __init__(self, length=10):
        list.__init__(self)
        RecognitionObserver.__init__(self)
        self._complete = True

        if (length is None or (isinstance(length, integer_types) and
                               length >= 1)):
            self._length = length
        else:
            raise ValueError("length must be a positive int or None,"
                             " received %r." % length)

    @property
    def complete(self):
        """ *False* if phrase-start detected but no recognition yet. """
        return self._complete

    def on_begin(self):
        """"""
        self._complete = False

    def on_recognition(self, words):
        """"""
        self._complete = True
        self.append(self._recognition_to_item(words))
        if self._length:
            while len(self) > self._length:
                self.pop(0)

    def _recognition_to_item(self, words):
        """"""
        # pylint: disable=no-self-use
        return words


#---------------------------------------------------------------------------

class PlaybackHistory(RecognitionHistory):
    """
        Storage class for playing back recent recognitions via the
        :class:`Playback` action.

        Instances of this class monitor recognitions and store them
        internally.  This class derives from the built in *list* type
        and can be accessed as if it were a normal *list* containing
        :class:`Playback` actions for recent recognitions.  Note that an
        instance's contents are updated automatically as recognitions are
        received.

    """

    def __init__(self, length=10):
        RecognitionHistory.__init__(self, length)

    def _recognition_to_item(self, words):
        return (words, time.time())

    def __getitem__(self, key):
        result = RecognitionHistory.__getitem__(self, key)
        if len(result) == 1:
            return Playback([(result[0][0], 0)])
        elif len(result) == 2 and isinstance(result[1], float):
            return Playback([(result[0], 0)])
        elif len(result) == 0:
            return Playback(())
        else:
            pairs = [(w1, t2 - t1)
                     for ((w1, t1), (w2, t2))
                     in zip(result[:-1], result[1:])]
            pairs.append((result[-1][0], 0))
            return Playback(pairs)

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

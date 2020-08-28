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
Mimic action
============================================================================


The :class:`Mimic` action mimics a single recognition.  This is useful for
repeating a single prerecorded or predefined voice-command.

This class could for example be used to open a new Windows Explorer window::

    action = Mimic("open", "windows", "explorer")
    action.execute()


A more in-depth example is given below in the class reference.


Mimic quirks
----------------------------------------------------------------------------

Some SR engine back-ends have confusing :meth:`engine.mimic` method
behavior.  See the engine-specific mimic method documentation in sections
under :ref:`RefEngines` for more information.


Class reference
----------------------------------------------------------------------------

"""
from six               import string_types
from .action_base      import ActionBase, ActionError
from ..engines         import get_engine


# ---------------------------------------------------------------------------

class Mimic(ActionBase):
    """
        Mimic recognition action.

        The constructor arguments are the words which will be mimicked.
        These should be passed as a variable argument list.  For example::

            action = Mimic("hello", "world", r"!\\exclamation-mark")
            action.execute()

        If an error occurs during mimicking the given recognition, then an
        *ActionError* is raised.  A common error is that the engine does
        not know the given words and can therefore not recognize them.
        For example, the following attempts to mimic recognition of *one
        single word* including a space and an exclamation-mark; this will
        almost certainly fail::

            Mimic("hello world!").execute()   # Will raise ActionError.

        The constructor accepts the optional *extra* keyword argument, and
        uses this to retrieve dynamic data from the extras associated with
        the recognition.  For example, this can be used as follows to
        implement dynamic mimicking::

            class ExampleRule(MappingRule):
                mapping  = {
                            "mimic recognition <text> [<n> times]":
                                Mimic(extra="text") * Repeat(extra="n"),
                           }
                extras   = [
                            IntegerRef("n", 1, 10),
                            Dictation("text"),
                           ]
                defaults = {
                            "n": 1,
                           }

        The example above will allow the user to speak **"mimic
        recognition hello world! 3 times"**, which would result in the
        exact same output as if the user had spoken **"hello world!"**
        three times in a row.

    """

    def __init__(self, *words, **kwargs):
        ActionBase.__init__(self)
        self._words = tuple(words)
        if "extra" in kwargs:
            self._extra = kwargs.pop("extra")
        else:
            self._extra = None

        # Set pretty printing string used by __str__ and __unicode__.
        self._str = u", ".join(repr(w) for w in self._words)

        # Make sure that all keyword arguments have been consumed.
        if kwargs:
            raise ActionError("Invalid arguments: %r"
                              % ", ".join(list(kwargs.keys())))

    def _execute(self, data=None):
        engine = get_engine()
        words = self._words

        # If an extra was given, retrieve the associated value from
        #  the *data* dict and append it to the static words.
        if self._extra:
            try:
                extra = data[self._extra]
            except KeyError:
                raise ActionError("No extra data available for extra %r"
                                  % self._extra)

            # Append the extra data to the static words depending on
            #  the type of the extra data object.
            if isinstance(extra, engine.DictationContainer):
                words += tuple(extra.words)
            elif isinstance(extra, (tuple, list)):
                words += tuple(extra)
            elif isinstance(extra, string_types):
                words += (extra,)
            else:
                raise ActionError("Invalid extra data type: %r" % extra)

        # Mimic the series of words.
        self._log.debug("Mimicking recognition: %r", words)
        try:
            engine.disable_recognition_observers()
            engine.mimic(words)
            engine.enable_recognition_observers()
        except Exception as e:
            raise ActionError("Mimicking failed: %s" % e)

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
Dictation container for the Kaldi engine.

"""

import itertools

from six import text_type

from ...grammar.elements_basic import Dictation as BaseDictation
from ...grammar.elements_basic import ElementBase, RuleRef, Alternative, ListRef, DictListRef, Repetition
from ...grammar.list import List, DictList
from ...grammar.rule_compound import CompoundRule


#---------------------------------------------------------------------------
# User dictation class -- elements capable of also recognizing user words.

class UserDictation(RuleRef):
    """
        Imitates the standard Dictation element class, using individual chunks
        of Dictation or the user's added terminology.
    """

    # Partially copied from BaseDictation
    def __init__(self, name=None, format=True, default=None):
        RuleRef.__init__(self, rule=_user_dictation_sequence_rule, name=name, default=default)
        self._format_words = format
        self._string_methods = []

    # Use BaseDictation methods
    __repr__ = BaseDictation.__repr__
    __getattr__ = BaseDictation.__getattr__

    # Partially copied from BaseDictation
    def value(self, node):
        words = node.children[0].value()
        if self._format_words:
            return node.engine.DictationContainer(words, self._string_methods)
        else:
            return words

user_dictation_list = List('__kaldi_user_dictation_list', [])
user_dictation_dictlist = DictList('__kaldi_user_dictation_dictlist', {})

class _UserDictationSequenceRule(CompoundRule):
    spec = "<__kaldi_user_dictation_sequence>"
    extras = [
        Repetition(Alternative([
            BaseDictation(format=False),
            ListRef('__kaldi_user_dictation_listref', user_dictation_list),
            DictListRef('__kaldi_user_dictation_dictlistref', user_dictation_dictlist),
        ]), min=1, max=16, name="__kaldi_user_dictation_sequence"),
    ]
    exported = False
    def value(self, node):
        # This method returns the value of the root Repetition: a list of values of
        # Alternatives, each (dictation or listref or dictlistref) being a string.
        chunks = node.children[0].value()
        # Make sure each chunk is a list (of strings), then concat them together.
        return list(itertools.chain.from_iterable([chunk] if not isinstance(chunk, list) else chunk for chunk in chunks))

_user_dictation_sequence_rule = _UserDictationSequenceRule()


#---------------------------------------------------------------------------
# Alternative dictation classes -- elements capable of default or alternative dictation.

class AlternativeDictation(BaseDictation):

    alternative_default = True

    def __init__(self, *args, **kwargs):
        self.alternative = kwargs.pop('alternative', self.alternative_default)
        BaseDictation.__init__(self, *args, **kwargs)

class DefaultDictation(BaseDictation):

    alternative_default = False

    def __init__(self, *args, **kwargs):
        self.alternative = kwargs.pop('alternative', self.alternative_default)
        BaseDictation.__init__(self, *args, **kwargs)

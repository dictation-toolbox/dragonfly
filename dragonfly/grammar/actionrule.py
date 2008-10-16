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
    This file implements the ActionRule class for simple
    utterance -> action rules.
"""


import dragonfly.grammar.rule as rule_
import dragonfly.grammar.elements as elements_
import dragonfly.grammar.context as context_
import dragonfly.actions.acstr as acstr_
import dragonfly.actions.keyboard


class ActionRule(rule_.Rule):

    _action_key = "_ActionRule_acstr"

    def __init__(self, name, action_map, prefix=None, suffix=None,
                 elements={}, actions={}, context=None, exported=False):
        assert isinstance(action_map, dict)
        assert isinstance(prefix, str) or prefix is None
        assert isinstance(suffix, str) or suffix is None
        assert isinstance(elements, dict) or elements is None
        assert isinstance(actions, dict) or actions is None
        assert isinstance(context, context_.Context) or context is None

        # Build action map.
        alternatives = []
        for key, value in action_map.items():
            element = elements_.Compound(key, elements, actions)
            action = elements_.Insert(self._action_key, value)
            element.add_action(action)
            alternatives.append(element)
        if len(alternatives) > 1:
            element = elements_.Alternative(alternatives)
        elif len(alternatives) == 1:
            element = alternatives[0]
        else:
            # To do: change this into some useful exception.
            raise Exception

        # Build prefix and suffix elements.
        sequence = [element]
        if prefix:
            prefix = elements_.Compound(prefix, elements, actions)
            sequence.insert(0, prefix)
        if suffix:
            suffix = elements_.Compound(suffix, elements, actions)
            sequence.append(suffix)
        if len(sequence) > 1:
            element = elements_.Sequence(sequence)
        else:
            element = sequence[0]

        rule_.Rule.__init__(self, name, element, context=context,
            exported=exported)

    def process_results(self, data):
        try: action = data[self._action_key]
        except KeyError: raise

        if self._log_proc:
            self._log_proc.debug("Executing action: %s" % action)

        action.execute(data)

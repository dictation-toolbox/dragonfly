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
    This file implements Dragonfly's grammar compiler which turns
    dragonfly rules and elements into NaturallySpeaking's
    binary grammar format.
"""


import struct


class GrammarError(Exception):
    pass


class Compiler(object):

    # Numeric values used in the binary form of rule definitions.
    _start_type = 1; _end_type = 2
    _word_type = 3; _rule_type = 4; _list_type = 6
    _seq_value = 1; _alt_value = 2; _rep_value = 3; _opt_value = 4

    def __init__(self):
        self._words = []; self._lists = []; self._rules = []
        self._import_rules = []
        self._export_rules = []
        self._rule_definitions = {}

        self._current_rule_name = None
        self._current_rule_export = None
        self._current_rule_definition = None

    #-----------------------------------------------------------------------

    def start_rule_definition(self, name, exported=False):
        """start defining a rule."""

        # Make sure no rule is being defined at the moment.
        if self._current_rule_name:
            raise GrammarError("Cannot start defining a rule while" \
                               "a different rule is already being defined.")

        assert isinstance(name, str), "The rule name must be a string."
        self._current_rule_name = name
        self._current_rule_export = exported
        self._current_rule_definition = []

    def end_rule_definition(self):
        """End defining a rule."""

        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot end defining a rule when" \
                               " no rule is being defined.")

        # Make sure that no other rule has been defined with this name.
        if self._current_rule_name in self._rule_definitions:
            raise GrammarError("Rule '%s' defined more than once." % \
                                self._current_rule_name)

        # If this rule has not been used before, register it.
        if self._current_rule_name not in self._rules:
            self._rules.append(self._current_rule_name)
        if self._current_rule_export:
            self._export_rules.append(self._current_rule_name)
        self._rule_definitions[self._current_rule_name] = \
            self._current_rule_definition

        self._current_rule_name = None
        self._current_rule_export = None
        self._current_rule_definition = None

    #-----------------------------------------------------------------------
    # Compound structures in a rule definition.

    def start_sequence(self):
        """start a sequence structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot start a sequence because" \
                               " no rule is currently being defined.")
        # Append the start-tag.
        self._current_rule_definition.append(
            (self._start_type, self._seq_value) )

    def end_sequence(self):
        """End a sequence structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot end a sequence because" \
                               " no rule is currently being defined.")
        # Append the end-tag.
        self._current_rule_definition.append(
            (self._end_type, self._seq_value) )

    def start_alternative(self):
        """start an alternative structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot start an alternative because" \
                               " no rule is currently being defined.")
        # Append the start-tag.
        self._current_rule_definition.append(
            (self._start_type, self._alt_value) )

    def end_alternative(self):
        """End an alternative structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot end an alternative because" \
                               " no rule is currently being defined.")
        # Append the end-tag.
        self._current_rule_definition.append(
            (self._end_type, self._alt_value) )

    def start_repetition(self):
        """start a repetition structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot start a repetition because" \
                               " no rule is currently being defined.")
        # Append the start-tag.
        self._current_rule_definition.append(
            (self._start_type, self._rep_value) )

    def end_repetition(self):
        """End a repetition structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot end a repetition because" \
                               " no rule is currently being defined.")
        # Append the end-tag.
        self._current_rule_definition.append(
            (self._end_type, self._rep_value) )

    def start_optional(self):
        """start a optional structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot start a optional because" \
                               " no rule is currently being defined.")
        # Append the start-tag.
        self._current_rule_definition.append(
            (self._start_type, self._opt_value) )

    def end_optional(self):
        """End a optional structure in the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot end a optional because" \
                               " no rule is currently being defined.")
        # Append the end-tag.
        self._current_rule_definition.append(
            (self._end_type, self._opt_value) )

    #-----------------------------------------------------------------------
    # Terminal elements in a rule definition.

    def add_word(self, word):
        """Append a literal word to the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot add word '%s' because" \
                               " no rule is currently being defined." % word)
        # Determine this word's ID.  If this word has not been used before,
        # register it.
        if word not in self._words:
            self._words.append(word)
            id = len(self._words)
        else:
            id = self._words.index(word) + 1
        # Append the word to the rule currently being defined.
        self._current_rule_definition.append( (self._word_type, id) )

    def add_list(self, list):
        """Append a list to the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot add list '%s' because" \
                               " no rule is currently being defined." % list)
        # Determine this list's ID.  If this list has not been used before,
        # register it.
        if list not in self._lists:
            self._lists.append(list)
            id = len(self._lists)
        else:
            id = self._lists.index(list) + 1
        # Append the list to the rule currently being defined.
        self._current_rule_definition.append( (self._list_type, id) )

    def add_rule(self, rule, imported = False):
        """Append a rule reference to the rule currently being defined."""
        # Make sure a rule is being defined at the moment.
        if not self._current_rule_name:
            raise GrammarError("Cannot add rule '%s' because" \
                               " no rule is currently being defined." % rule)
        # Determine this rule's ID.  If this rule has not been used before,
        # register it.
        if rule not in self._rules:
            self._rules.append(rule)
            if imported: self._import_rules.append(rule)
            id = len(self._rules)
        # If this rule has been referenced multiple times, make sure that
        # it has either always being imported or never been imported.
        elif imported != (rule in self._import_rules):
            raise GrammarError("Rule '%s' cannot be referenced as both" \
                               " imported and not imported within a" \
                               " grammar." % rule)
        else:
            id = self._rules.index(rule) + 1
        # Append the rule to the rule currently being defined.
        self._current_rule_definition.append( (self._rule_type, id) )

    #-----------------------------------------------------------------------

    def compile(self):
        """Compile a binary grammar of this compiler's current state."""

        # Make sure no rule is being defined at the moment.
        if self._current_rule_name:
            raise GrammarError("Cannot compile grammar while a rule" \
                               " is being defined.")

        # Grammar header:
        #   - dwType; use 0.
        #   - dwFlags; use 0.
        output = [struct.pack("LL", 0, 0)]

        # Lists of the names and IDs of exports, imports, lists, and words.
        output.append(self._compile_id_chunk(4, self._export_rules, self._rules))
        output.append(self._compile_id_chunk(5, self._import_rules, self._rules))
        output.append(self._compile_id_chunk(6, self._lists, self._lists))
        output.append(self._compile_id_chunk(2, self._words, self._words))

        # List of rule definitions.
        output.append(self._compile_rule_chunk(3))

        # Return a concatenation of the header and chunks.
        return "".join(output)

    def _compile_id_chunk(self, chunk_id, subset, ordered_superset):
        # Loop through the elements of the superset, and if also present in
        #  the subset create a data entry of its ID and name.  The IDs start
        #  counting at 1.
        elements = []
        for name, id in zip(ordered_superset,
                            xrange(1, len(ordered_superset) + 1)):

            # Skip names not included in the subset.
            if name not in subset: continue

            # Chunk element:
            #  - dwSize; size of this element in bytes including this header.
            #  - dwNum; the element's ID.
            #  - szName; the element's name terminated by at least one 0.
            # The element's name must be followed by one or more 0
            #  characters, so that its size in bytes is a multiple of 4.
            padded_len = (len(name) + 4) & (~3)
            element = struct.pack("LL%ds" % padded_len,
                padded_len + 8, id, name)
            elements.append(element)

        # Concatenate all the elements.
        element_data = "".join(elements)

        # Chunk header:
        #  - dwChunkId; words:2, rule definitions:3,
        #     exports:4, imports:5, lists:6
        #  - dwChunkSize; size of this chunk in bytes excluding this header.
        header = struct.pack("LL", chunk_id, len(element_data))

        # Return the header and the elements.
        return header + element_data

    def _compile_rule_chunk(self, chunk_id):
        # Loop through all known rule names, and if they are defined within
        #  this grammar create a rule definition entry.
        definitions = []
        for name, id in zip(self._rules,
                            xrange(1, len(self._rules) + 1)):

            # Skip imported rules.
            if name in self._import_rules:
                if name in self._rule_definitions:
                    raise GrammarError("Rule '%s' cannot be both imported" \
                                        " and defined in a grammar" % name)
                continue

            # Make sure that a definition has been given.
            if name not in self._rule_definitions:
                raise GrammarError("Rule '%s' is neither imported" \
                                    " nor defined" % name)
    
            # Build the definition sequence for this rule.  
            elements = []
            for t, v in self._rule_definitions[name]:
                # Definition element:
                #  - wType; start:1, end:2, word:3, rule:4, list:6
                #  - wProb; probability rating, use 0.
                #  - dwValue; depends on wType as follows:
                #     - if wType is start or end, then dwValue is one of
                #        sequence:1, alternative:2, repetition:3, optional:4
                #     - if wType is word, rule, or list, then dwValue is
                #        the ID of the corresponding element.
                element = struct.pack("HHL", t, 0, v)
                elements.append(element)

            # Definition header:
            #  - dwSize; size of this rule definition in bytes including
            #     this header.
            #  - dwNum; the ID of this rule.
            definition_size = 8 + sum([len(s) for s in elements])
            definition = struct.pack("LL", definition_size, id)
            definition += "".join(elements)

            definitions.append(definition)

        # Concatenate all the rule definitions.
        definition_data = "".join(definitions)

        # Rule definition chunk header:
        #  - dwChunkId; rule definitions:3
        #  - dwChunkSize; size of this chunk in bytes excluding this header.
        header = struct.pack("LL", chunk_id, len(definition_data))

        # Return the header and the rule definitions.
        return header + definition_data

    def _get_rule_names(self):
        return tuple([None] + self._rules)

    rule_names = property(_get_rule_names,
                doc="Read-only access to the list of rule names.")

    #-----------------------------------------------------------------------

    def debug_state_string(self):
        """Debug."""

        import textwrap
        wrapper = textwrap.TextWrapper(subsequent_indent = "   ")
        output = []

        wrapper.initial_indent = "exported rules: "
        output.append(wrapper.wrap(", ".join(self._export_rules)))
        wrapper.initial_indent = "imported rules: "
        output.append(wrapper.wrap(", ".join(self._import_rules)))
        wrapper.initial_indent = "lists: "
        output.append(wrapper.wrap(", ".join(self._lists)))
        wrapper.initial_indent = "words: "
        output.append(wrapper.wrap(", ".join(self._words)))
        wrapper.initial_indent = "rule definitions: "
        output.append(wrapper.wrap(str(self._rule_definitions)))

        return "\n".join(["\n".join(lines) for lines in output if lines])

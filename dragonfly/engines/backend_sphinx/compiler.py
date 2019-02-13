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
Compilers for JSpeech Grammar Format (JSGF) and the CMU Pocket Sphinx speech
recognition engine.
"""

import jsgf
import jsgf.ext
from dragonfly import List, DictList
import dragonfly.grammar.elements as elements_

from ..base import CompilerBase, CompilerError

# noinspection PyUnusedLocal


class JSGFCompiler(CompilerBase):
    """
    Dragonfly compiler for JSpeech Grammar Format (JSGF)

    This class translates dragonfly elements, rules and grammars into
    JSGF expansions, rules and grammars respectively.
    """

    GrammarClass = jsgf.Grammar

    @staticmethod
    def get_reference_name(o):
        # Return a non-nil name string.
        if not o.name:
            name = o.__class__.__name__
        else:
            name = o.name
        return name

    # ----------------------------------------------------------------------
    # Methods for compiling grammars and rules.

    def compile_grammar(self, grammar, *args, **kwargs):
        """
        Take a dragonfly grammar and translate it into a JSGF grammar object
        with methods for compiling the grammar and matching speech.

        :param grammar:
        :param args:
        :param kwargs:
        :return:
        """
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        # Create a new JSGF Grammar object.
        result = self.GrammarClass(name=self.get_reference_name(grammar))

        # Compile each dragonfly rule and add it to the new grammar.
        for rule in grammar.rules:
            result.add_rule(self.compile_rule(rule))

        # Also compile and add any dragonfly Lists.
        for lst in grammar.lists:
            result.add_rule(self.compile_list(lst))

        # Return None for empty grammars.
        if not result.rules:
            return

        return result

    def compile_rule(self, rule):
        return jsgf.Rule(name=self.get_reference_name(rule),
                         visible=rule.exported,
                         expansion=self.compile_element(rule.element))

    # ----------------------------------------------------------------------
    # Method for compiling dragonfly lists and dictionary lists.
    # These have no equivalent in JSGF, so hidden/private rules are used
    # instead.

    def compile_list(self, lst):
        if isinstance(lst, List):
            literal_list = [elements_.Literal(item) for item in lst]
        elif isinstance(lst, DictList):
            keys = list(lst.keys())
            keys.sort()
            literal_list = [elements_.Literal(key) for key in keys]
        else:
            raise CompilerError("Cannot compile dragonfly List %s"
                                % lst)

        return jsgf.HiddenRule(
            self.get_reference_name(lst),
            self.compile_element(elements_.Alternative(literal_list))
        )

    # ----------------------------------------------------------------------
    # Methods for compiling elements.

    def compile_element(self, element, *args, **kwargs):
        # Look for a compiler method to handle the given element.
        for element_type, compiler in self.element_compilers:
            if isinstance(element, element_type):
                return compiler(self, element, *args, **kwargs)

        # Didn't find a compiler method for this element type.
        raise NotImplementedError("Compiler %s not implemented"
                                  " for element type %s."
                                  % (self, element))

    def _compile_repetition(self, element):
        # Compile the first element only; pyjsgf doesn't support limits on
        # repetition (yet).
        children = element.children
        if len(children) > 1:
            self._log.debug("Ignoring limits of repetition element %s."
                            % element)
        return jsgf.Repeat(self.compile_element(children[0]))

    def _compile_sequence(self, element):
        # Compile Repetition elements separately.
        if isinstance(element, elements_.Repetition):
            return self._compile_repetition(element)

        children = element.children
        if len(children) > 1:
            return jsgf.Sequence(*[self.compile_element(c)
                                   for c in children])
        elif len(children) == 1:
            # Skip redundant (1 child) sequences.
            return self.compile_element(children[0])
        else:
            # Compile an Empty element for empty sequences.
            return self.compile_element(elements_.Empty())

    def _compile_alternative(self, element):
        children = element.children
        if len(children) > 1:
            return jsgf.AlternativeSet(*[self.compile_element(c)
                                         for c in children])
        elif len(children) == 1:
            # Skip redundant (1 child) alternatives.
            return self.compile_element(children[0])
        else:
            # Compile an Empty element for empty alternatives.
            return self.compile_element(elements_.Empty())

    def _compile_optional(self, element):
        child = element.children[0]
        return jsgf.OptionalGrouping(self.compile_element(child))

    def _compile_literal(self, element):
        return jsgf.Literal(" ".join(element.words))

    def _compile_rule_ref(self, element):
        name = element.rule.name
        return jsgf.NamedRuleRef(name)

    def _compile_list_ref(self, element):
        name = element.list.name
        return jsgf.NamedRuleRef(name)

    def _compile_empty(self, element):
        return jsgf.NullRef()

    def _compile_impossible(self, element):
        # Note: this will disable the entire rule and the entire grammar if
        # it was compiled as a 'root' grammar.
        return jsgf.VoidRef()


class PatchedRepeat(jsgf.Repeat):
    """
    Repeat class patched to compile JSGF repeats as
    "expansion [expansion]*" to avoid a bug in Pocket Sphinx with the
    repeat operator.
    """
    def compile(self, ignore_tags=False):
        super(PatchedRepeat, self).compile()
        compiled = self.child.compile(ignore_tags)
        if self.tag and not ignore_tags:
            return "(%s)[%s]*%s" % (compiled, compiled, self.tag)
        else:
            return "(%s)[%s]*" % (compiled, compiled)


class SphinxJSGFCompiler(JSGFCompiler):
    """
    JSGF compiler sub-class used by the CMU Pocket Sphinx backend.
    """

    # ----------------------------------------------------------------------
    # Methods for compiling elements.

    def _compile_repetition(self, element):
        # Compile the first element only; pyjsgf doesn't support limits on
        # repetition (yet).
        children = element.children
        if len(children) > 1:
            self._log.debug("Ignoring limits of repetition element %s."
                            % element)

        # Return a PatchedRepeat instead of a normal Repeat expansion.
        return PatchedRepeat(self.compile_element(children[0]))

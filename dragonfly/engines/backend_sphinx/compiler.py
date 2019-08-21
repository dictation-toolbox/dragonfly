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
        if hasattr(o, "name"):
            if not o.name:
                name = o.__class__.__name__
            else:
                name = o.name
        else:
            # Assume the object is a string.
            name = o

        # JSGF and Pocket Sphinx don't allow spaces in names, but dragonfly
        # does. Work around this by changing any spaces to underscores.
        return name.replace(" ", "_")

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
        unknown_words = set()
        result = self.GrammarClass(name=self.get_reference_name(grammar))

        # Compile each dragonfly rule and add it to the new grammar.
        for rule in grammar.rules:
            result.add_rule(self.compile_rule(rule, result, unknown_words))

        # Also compile and add any dragonfly Lists.
        for lst in grammar.lists:
            result.add_rule(self.compile_list(lst, result, unknown_words))

        # Log a warning about unknown words if necessary.
        if unknown_words:
            self._log.warning("Grammar '%s' used words not found in the "
                              "pronunciation dictionary: %s", result.name,
                              ", ".join(sorted(unknown_words)))

        # Return None for empty grammars.
        if not result.rules:
            return

        return result

    def compile_rule(self, rule, *args, **kwargs):
        return jsgf.Rule(
            name=self.get_reference_name(rule),
            visible=rule.exported,
            expansion=self.compile_element(rule.element, *args, **kwargs)
        )

    # ----------------------------------------------------------------------
    # Methods for compiling dragonfly lists and dictionary lists.
    # These have no equivalent in JSGF, so hidden/private rules are used
    # instead.

    def compile_list(self, lst, *args, **kwargs):
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
            self.compile_element(elements_.Alternative(literal_list), *args,
                                 **kwargs)
        )

    def recompile_list(self, lst, jsgf_grammar):
        # Used from the GrammarWrapper class to get an updated list and any
        # unknown words.
        unknown_words = set()
        return (self.compile_list(lst, jsgf_grammar, unknown_words),
                unknown_words)

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

    def _compile_repetition(self, element, *args, **kwargs):
        # Compile the first element only; pyjsgf doesn't support limits on
        # repetition (yet).
        children = element.children
        if len(children) > 1:
            self._log.debug("Ignoring limits of repetition element %s."
                            % element)
        compiled_child = self.compile_element(children[0], *args, **kwargs)
        return jsgf.Repeat(compiled_child)

    def _compile_sequence(self, element, *args, **kwargs):
        # Compile Repetition elements separately.
        if isinstance(element, elements_.Repetition):
            return self._compile_repetition(element, *args, **kwargs)

        children = element.children
        if len(children) > 1:
            return jsgf.Sequence(*[
                self.compile_element(c, *args, **kwargs) for c in children
            ])
        elif len(children) == 1:
            # Skip redundant (1 child) sequences.
            return self.compile_element(children[0], *args, **kwargs)
        else:
            # Compile an Empty element for empty sequences.
            return self.compile_element(elements_.Empty(), *args, **kwargs)

    def _compile_alternative(self, element, *args, **kwargs):
        children = element.children
        if len(children) > 1:
            return jsgf.AlternativeSet(*[
                self.compile_element(c, *args, **kwargs) for c in children
            ])
        elif len(children) == 1:
            # Skip redundant (1 child) alternatives.
            return self.compile_element(children[0], *args, **kwargs)
        else:
            # Compile an Empty element for empty alternatives.
            return self.compile_element(elements_.Empty(), *args, **kwargs)

    def _compile_optional(self, element, *args, **kwargs):
        child = self.compile_element(element.children[0], *args, **kwargs)
        return jsgf.OptionalGrouping(child)

    def _compile_literal(self, element, *args, **kwargs):
        return jsgf.Literal(" ".join(element.words))

    def _compile_rule_ref(self, element, *args, **kwargs):
        name = element.rule.name.replace(" ", "_")
        return jsgf.NamedRuleRef(name)

    def _compile_list_ref(self, element, *args, **kwargs):
        name = element.list.name.replace(" ", "_")
        return jsgf.NamedRuleRef(name)

    def _compile_empty(self, element, *args, **kwargs):
        return jsgf.NullRef()

    def _compile_impossible(self, element, *args, **kwargs):
        return jsgf.VoidRef()

    def _compile_dictation(self, element, *args, **kwargs):
        # JSGF has no equivalent for dictation elements. Instead compile and
        # return an Impossible element that allows dictation to be used,
        # but not matched.
        return self.compile_element(
            elements_.Impossible(), *args, **kwargs
        )


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

    def __init__(self, engine):
        JSGFCompiler.__init__(self)
        self.engine = engine

        # Use a very unlikely phrase to replace unknown words. NullRefs are
        # used instead if words aren't in the vocabulary.
        self.impossible_literal = {
            "en": "impossible " * 20,
        }.get(engine.language, "")

    # ----------------------------------------------------------------------
    # Methods for compiling elements.

    def _compile_repetition(self, element, *args, **kwargs):
        # Compile the first element only; pyjsgf doesn't support limits on
        # repetition (yet).
        children = element.children
        if len(children) > 1:
            self._log.debug("Ignoring limits of repetition element %s."
                            % element)

        # Return a PatchedRepeat instead of a normal Repeat expansion.
        compiled_child = self.compile_element(children[0], *args, **kwargs)
        return PatchedRepeat(compiled_child)

    def _compile_literal(self, element, *args, **kwargs):
        # Build literals as sequences and use <NULL> for unknown words.
        children = []
        for word in element.words:
            if self.engine.check_valid_word(word):
                children.append(jsgf.Literal(word))
            else:
                children.append(self.compile_element(
                    elements_.Impossible(), *args, **kwargs
                ))

                # Save the unknown word.
                args[1].add(word)

        return jsgf.Sequence(*children)

    def _compile_impossible(self, element, *args, **kwargs):
        # Override this to avoid VoidRefs disabling entire rules/grammars.
        # Use a special <_impossible> private rule instead. Only add the
        # special rule if it isn't in the result grammar.
        grammar = args[0]
        if "_impossible" not in grammar.rule_names:
            # Check that the impossible literal contains only valid words.
            words = set(self.impossible_literal.split())
            valid_literal = bool(words)
            for word in words:
                if not valid_literal:
                    break
                if not self.engine.check_valid_word(word):
                    valid_literal = False

            if valid_literal:
                expansion = jsgf.Literal(self.impossible_literal)
            else:
                # Fallback on a NullRef. There are some problems with using
                # these, but they get the job done for simple rules.
                expansion = jsgf.NullRef()
            grammar.add_rule(jsgf.Rule(
                name="_impossible", visible=False, expansion=expansion
            ))

        return jsgf.NamedRuleRef("_impossible")

    # TODO Change this to allow dictation elements to work.
    def _compile_dictation(self, element, *args, **kwargs):
        return self.compile_element(
            elements_.Impossible(), *args, **kwargs
        )

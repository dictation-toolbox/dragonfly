#
# This file is part of Dragonfly.
# (c) Copyright 2019 by David Zurow
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
Compiler classes for Kaldi backend
"""

import collections, logging, os.path, re, subprocess

from .testing                   import debug_timer
from ..base                     import CompilerBase, CompilerError
from ...grammar.rule_base       import Rule
from ...grammar.elements_basic  import Impossible, Literal

import six
import pyparsing as pp
from kaldi_active_grammar import WFST, KaldiRule
from kaldi_active_grammar import Compiler as KAGCompiler

_log = logging.getLogger("engine.compiler")


#---------------------------------------------------------------------------
# Utilities

_trace_level=0
def trace_compile(func):
    return func
    def dec(self, element, src_state, dst_state, grammar, fst):
        global _trace_level
        s = '%s %s: compiling %s' % (grammar.name, '==='*_trace_level, element)
        l = 140-len(s)
        s += ' '*l + '| %-20s %s -> %s' % (id(fst), src_state, dst_state)
        grammar._log_load.error(s)
        _trace_level+=1
        ret = func(self, element, src_state, dst_state, grammar, fst)
        _trace_level-=1
        grammar._log_load.error('%s %s: compiling %s.' % (grammar.name, '...'*_trace_level, element))
        return ret
    return dec

InternalGrammar = collections.namedtuple('InternalGrammar', 'name')
InternalRule = collections.namedtuple('InternalRule', 'name gstring')


#---------------------------------------------------------------------------

class KaldiCompiler(CompilerBase, KAGCompiler):

    def __init__(self, model_dir, tmp_dir):
        CompilerBase.__init__(self)
        KAGCompiler.__init__(self, model_dir, tmp_dir)

        self.kaldi_rule_by_rule_dict = collections.OrderedDict()  # maps Rule -> KaldiRule
        self._grammar_rule_states_dict = dict()  # FIXME: disabled!
        self.internal_grammar = InternalGrammar('!kaldi_engine_internal')

        self._compile_base_fsts()

    impossible_word = property(lambda self: self._longest_word)
    unknown_word = '<unk>'

    #-----------------------------------------------------------------------
    # Methods for handling lexicon translation.

    translation_dict = {
    }

    untranslation_dict = { v: k for k, v in translation_dict.items() }
    translation_dict.update({
    })

    def untranslate_output(self, output):
        for old, new in self.untranslation_dict.iteritems():
            output = output.replace(old, new)
        return output

    def translate_words(self, words):
        new_words = []
        for word in words:
            for old, new in self.translation_dict.iteritems():
                word = word.replace(old, new)
            word = word.lower()
            new_words.extend(word.split())
        words = new_words
        new_words = []
        for word in words:
            if word not in self._lexicon_words:
                self._log.warning("%s: Word not in lexicon (will not be recognized): %r" % (self, word))
                word = self.impossible_word
            new_words.append(word)
        return new_words

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, engine):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        kaldi_rule_by_rule_dict = collections.OrderedDict()
        for rule in grammar.rules:
            if rule.exported:
                kaldi_rule_id = self._num_kaldi_rules
                self._num_kaldi_rules += 1
                kaldi_rule = KaldiRule(self, kaldi_rule_id, name='%s::%s' % (grammar.name, rule.name), dictation=bool('<Dictation()>' in rule.gstring()))
                kaldi_rule.grammar = grammar
                kaldi_rule.rule = rule
                matcher, _, _ = self._compile_rule(rule, grammar, kaldi_rule.fst)
                kaldi_rule.matcher = matcher.setName(str(kaldi_rule_id)).setResultsName(str(kaldi_rule_id))
                kaldi_rule.fst.equalize_weights()
                kaldi_rule.compile_file()
                self.kaldi_rule_by_id_dict[kaldi_rule_id] = kaldi_rule
                self.kaldi_rule_by_rule_dict[rule] = kaldi_rule
                kaldi_rule_by_rule_dict[rule] = kaldi_rule

        return kaldi_rule_by_rule_dict

    def _compile_rule(self, rule, grammar, fst, export=True):
        # Determine whether this rule has already been compiled.
        if (grammar.name, rule.name) in self._grammar_rule_states_dict:
            self._log.debug("%s: Already compiled rule %s%s." % (self, rule.name, ' [EXPORTED]' if export else ''))
            return self._grammar_rule_states_dict[(grammar.name, rule.name)]
        else:
            self._log.debug("%s: Compiling rule %s%s." % (self, rule.name, ' [EXPORTED]' if export else ''))

        src_state = fst.add_state(initial=export)
        dst_state = fst.add_state(final=export)
        matcher = self.compile_element(rule.element, src_state, dst_state, grammar, fst)
        matcher = matcher.setName(rule.name).setResultsName(rule.name)

        # self._grammar_rule_states_dict[(grammar.name, rule.name)] = (matcher, src_state, dst_state)
        return (matcher, src_state, dst_state)

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    def compile_element(self, element, *args, **kwargs):
        """Compile element in FST (from src_state to dst_state) and return matcher for element (used in parsing kaldi output)."""
        # Look for a compiler method to handle the given element.
        for element_type, compiler in self.element_compilers:
            if isinstance(element, element_type):
                return compiler(self, element, *args, **kwargs)
        # Didn't find a compiler method for this element type.
        raise NotImplementedError("Compiler %s not implemented for element type %s." % (self, element))

    @trace_compile
    def _compile_sequence(self, element, src_state, dst_state, grammar, fst):
        # "insert" new states for individual children elements
        states = [src_state] + [fst.add_state() for i in range(len(element.children)-1)] + [dst_state]
        matchers = []
        for i, child in enumerate(element.children):
            s1 = states[i]
            s2 = states[i + 1]
            matchers.append(self.compile_element(child, s1, s2, grammar, fst))
        return pp.And(tuple(matchers))

    @trace_compile
    def _compile_alternative(self, element, src_state, dst_state, grammar, fst):
        matchers = []
        for child in element.children:
            matchers.append(self.compile_element(child, src_state, dst_state, grammar, fst))
        return pp.Or(tuple(matchers))

    @trace_compile
    def _compile_optional(self, element, src_state, dst_state, grammar, fst):
        matcher = self.compile_element(element.children[0], src_state, dst_state, grammar, fst)
        fst.add_arc(src_state, dst_state, None)
        return pp.Optional(matcher)

    @trace_compile
    def _compile_literal(self, element, src_state, dst_state, grammar, fst):
        # "insert" new states for individual words
        words = element.words
        matcher = pp.CaselessLiteral(' '.join(words))
        words = self.translate_words(words)
        states = [src_state] + [fst.add_state() for i in range(len(words)-1)] + [dst_state]
        for i, word in enumerate(words):
            s1 = states[i]
            s2 = states[i + 1]
            fst.add_arc(s1, s2, word.lower())
        return matcher

    @trace_compile
    def _compile_rule_ref(self, element, src_state, dst_state, grammar, fst):
        matcher, rule_src_state, rule_dst_state = self._compile_rule(element.rule, grammar, fst, export=False)
        fst.add_arc(src_state, rule_src_state, None)
        fst.add_arc(rule_dst_state, dst_state, None)
        return matcher

    # @trace_compile
    # def _compile_list_ref(self, element, src_state, dst_state, grammar, fst):
    #     list_rule_name = "__list_%s" % element.list.name
    #     rule_handle = grammar_handle.Rules.FindRule(list_rule_name)
    #     if not rule_handle:
    #         grammar.add_list(element.list)
    #         flags = constants.SRADynamic
    #         rule_handle = grammar_handle.Rules.Add(list_rule_name, flags, 0)
    #     src_state.AddRuleTransition(dst_state, rule_handle)

    @trace_compile
    def _compile_dictation(self, element, src_state, dst_state, grammar, fst):
        fst.add_arc(src_state, dst_state, '#nonterm:dictation', olabel=WFST.eps)
        return pp.OneOrMore(pp.Word(pp.alphas + pp.alphas8bit + pp.printables))

    @trace_compile
    def _compile_impossible(self, element, src_state, dst_state, grammar, fst):
        # FIXME: not impossible enough
        fst.add_arc(src_state, dst_state, self.impossible_word.lower())
        return pp.NoMatch()

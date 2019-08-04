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
from .dictation                 import CloudDictation, LocalDictation
from ..base                     import CompilerBase, CompilerError
from ...grammar                 import elements as elements_

import six
import pyparsing as pp
from kaldi_active_grammar import WFST, KaldiRule
from kaldi_active_grammar import Compiler as KaldiAGCompiler

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

MockLiteral = collections.namedtuple('MockLiteral', 'words')


#---------------------------------------------------------------------------

class KaldiCompiler(CompilerBase, KaldiAGCompiler):

    def __init__(self, model_dir, tmp_dir, auto_add_to_user_lexicon=None, **kwargs):
        CompilerBase.__init__(self)
        KaldiAGCompiler.__init__(self, model_dir, tmp_dir=tmp_dir, **kwargs)

        self.auto_add_to_user_lexicon = auto_add_to_user_lexicon

        self.kaldi_rule_by_rule_dict = collections.OrderedDict()  # maps Rule -> KaldiRule
        self._grammar_rule_states_dict = dict()  # FIXME: disabled!
        self.kaldi_rules_by_listreflist_dict = collections.defaultdict(set)
        self.added_word = False
        self.internal_grammar = InternalGrammar('!kaldi_engine_internal')

    impossible_word = property(lambda self: self._longest_word)  # FIXME
    unknown_word = '<unk>'

    #-----------------------------------------------------------------------
    # Methods for handling lexicon translation.

    # FIXME: documentation
    translation_dict = {
    }

    # FIXME: documentation
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
            if word not in self.lexicon_words:
                word = self.handle_oov_word(word)
            new_words.append(word)
        return new_words

    def handle_oov_word(self, word):
        if self.auto_add_to_user_lexicon:
            try:
                phones = self.model.add_word(word, lazy_compilation=True)
                self.added_word = True
            except Exception as e:
                self._log.exception("%s: exception automatically adding word %r" % (self, word))
            else:
                self._log.warning("%s: Word not in lexicon (generated automatic pronunciation): %r [%s]" % (self, word, ' '.join(phones)))
                return word

        self._log.warning("%s: Word %r not in lexicon (will NOT be recognized; see documentation about user lexicon and auto_add_to_user_lexicon)" % (self, word))
        word = self.impossible_word
        return word

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, engine):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        kaldi_rule_by_rule_dict = collections.OrderedDict()
        for rule in grammar.rules:
            if rule.exported:
                if rule.element is None:
                    raise CompilerError("Invalid None element for rule %s in grammar %s" % (rule, grammar))

                kaldi_rule = KaldiRule(self,
                    name='%s::%s' % (grammar.name, rule.name),
                    has_dictation=bool((rule.element is not None) and ('<Dictation()>' in rule.gstring())))
                kaldi_rule.parent_grammar = grammar
                kaldi_rule.parent_rule = rule

                self.kaldi_rule_by_rule_dict[rule] = kaldi_rule
                kaldi_rule_by_rule_dict[rule] = kaldi_rule

                self._compile_rule_root(rule, grammar, kaldi_rule)

        return kaldi_rule_by_rule_dict

    def _compile_rule_root(self, rule, grammar, kaldi_rule):
        matcher, _, _ = self._compile_rule(rule, grammar, kaldi_rule, kaldi_rule.fst)
        kaldi_rule.matcher = matcher.setName(str(kaldi_rule.name)).setResultsName(str(kaldi_rule.name))
        kaldi_rule.fst.equalize_weights()
        if self.added_word:
            self.model.load_words()
            self.model.generate_lexicon_files()
            self.decoder.load_lexicon()
            self.added_word = False
        kaldi_rule.compile_file()

    def _compile_rule(self, rule, grammar, kaldi_rule, fst, export=True):
        # Determine whether this rule has already been compiled.
        if (grammar.name, rule.name) in self._grammar_rule_states_dict:
            self._log.debug("%s: Already compiled rule %s%s." % (self, rule.name, ' [EXPORTED]' if export else ''))
            return self._grammar_rule_states_dict[(grammar.name, rule.name)]
        else:
            self._log.debug("%s: Compiling rule %s%s." % (self, rule.name, ' [EXPORTED]' if export else ''))

        src_state = fst.add_state(initial=export)
        dst_state = fst.add_state(final=export)
        matcher = self.compile_element(rule.element, src_state, dst_state, grammar, kaldi_rule, fst)
        matcher = matcher.setName(rule.name).setResultsName(rule.name)

        # self._grammar_rule_states_dict[(grammar.name, rule.name)] = (matcher, src_state, dst_state)
        return (matcher, src_state, dst_state)

    def unload_grammar(self, grammar, rules, engine):
        for rule in rules:
            kaldi_rule = self.kaldi_rule_by_rule_dict[rule]
            kaldi_rule.destroy()
            del self.kaldi_rule_by_rule_dict[rule]

    def update_list(self, lst, rules, grammar):
        # FIXME: it may be safe to just loop over this directly
        lst_kaldi_rules = self.kaldi_rules_by_listreflist_dict[id(lst)]
        for rule in rules:
            kaldi_rule = self.kaldi_rule_by_rule_dict[rule]
            if kaldi_rule in lst_kaldi_rules:
                with kaldi_rule.reload():
                    self._compile_rule_root(rule, grammar, kaldi_rule)

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
    def _compile_sequence(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        children = element.children
        if len(children) > 1:
            # Handle Repetition elements differently as a special case.
            is_rep = isinstance(element, elements_.Repetition)
            if is_rep and element.optimize:
                # Repetition...
                # Insert new states, so back arc only affects child
                s1 = fst.add_state()
                s2 = fst.add_state()
                fst.add_arc(src_state, s1, None)
                # NOTE: to avoid creating an un-decodable epsilon loop, we must not allow an all-epsilon child here (compile_graph_agf should check)
                matcher = self.compile_element(children[0], s1, s2, grammar, kaldi_rule, fst)
                # NOTE: has_eps_path is ~3-5x faster than matcher.parseString() inside try/except block
                if not fst.has_eps_path(s1, s2):
                    fst.add_arc(s2, s1, fst.eps_disambig, fst.eps)  # back arc
                    fst.add_arc(s2, dst_state, None)
                    return pp.OneOrMore(matcher)

                else:
                    # Cannot do optimize path, because of epsilon loop, so finish up with Sequence path
                    self._log.warning("%s: Cannot optimize Repetition element, because its child element can match empty string; falling back inefficient non-optimize path!" % self)
                    states = [src_state, s2] + [fst.add_state() for i in range(len(children)-2)] + [dst_state]
                    matchers = [matcher]
                    for i, child in enumerate(children[1:], start=1):
                        s1 = states[i]
                        s2 = states[i + 1]
                        matchers.append(self.compile_element(child, s1, s2, grammar, kaldi_rule, fst))
                    return pp.And(tuple(matchers))

            else:
                # Sequence...
                # Insert new states for individual children elements
                states = [src_state] + [fst.add_state() for i in range(len(children)-1)] + [dst_state]
                matchers = []
                for i, child in enumerate(children):
                    s1 = states[i]
                    s2 = states[i + 1]
                    matchers.append(self.compile_element(child, s1, s2, grammar, kaldi_rule, fst))
                return pp.And(tuple(matchers))

        elif len(children) == 1:
            return self.compile_element(children[0], src_state, dst_state, grammar, kaldi_rule, fst)

        else:  # len(children) == 0
            return pp.Empty()

    @trace_compile
    def _compile_alternative(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        matchers = []
        for child in element.children:
            matchers.append(self.compile_element(child, src_state, dst_state, grammar, kaldi_rule, fst))
        return pp.Or(tuple(matchers))

    @trace_compile
    def _compile_optional(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        matcher = self.compile_element(element.children[0], src_state, dst_state, grammar, kaldi_rule, fst)
        fst.add_arc(src_state, dst_state, None)
        return pp.Optional(matcher)

    @trace_compile
    def _compile_literal(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        # "insert" new states for individual words
        words = element.words
        words = map(str, words)  # FIXME: handle unicode
        matcher = pp.CaselessLiteral(' '.join(words))
        words = self.translate_words(words)
        states = [src_state] + [fst.add_state() for i in range(len(words)-1)] + [dst_state]
        for i, word in enumerate(words):
            s1 = states[i]
            s2 = states[i + 1]
            fst.add_arc(s1, s2, word.lower())
        return matcher

    @trace_compile
    def _compile_rule_ref(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        matcher, rule_src_state, rule_dst_state = self._compile_rule(element.rule, grammar, kaldi_rule, fst, export=False)
        fst.add_arc(src_state, rule_src_state, None)
        fst.add_arc(rule_dst_state, dst_state, None)
        return matcher

    @trace_compile
    def _compile_list_ref(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        # list_rule_name = "__list_%s" % element.list.name
        if element.list not in grammar.lists:
            # Should only happen during initial compilation; during updates, we must skip this
            grammar.add_list(element.list)
        self.kaldi_rules_by_listreflist_dict[id(element.list)].add(kaldi_rule)
        matchers = []
        for child_str in element.list.get_list_items():
            matchers.append(self._compile_literal(MockLiteral(child_str.split()), src_state, dst_state, grammar, kaldi_rule, fst))
        return pp.Or(tuple(matchers))

    @trace_compile
    def _compile_dictation(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        # fst.add_arc(src_state, dst_state, '#nonterm:dictation', olabel=WFST.eps)
        extra_state = fst.add_state()
        cloud_dictation = isinstance(element, (CloudDictation, LocalDictation)) and element.cloud
        cloud_dictation_nonterm = '#nonterm:dictation_cloud' if cloud_dictation else '#nonterm:dictation'
        fst.add_arc(src_state, extra_state, '#nonterm:dictation', cloud_dictation_nonterm)
        fst.add_arc(extra_state, dst_state, WFST.eps, '#nonterm:end')
        return pp.OneOrMore(pp.Word(pp.alphas + pp.alphas8bit + pp.printables))

    @trace_compile
    def _compile_impossible(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        # FIXME: not impossible enough (lower probability?)
        fst.add_arc(src_state, dst_state, self.impossible_word.lower())
        return pp.NoMatch()

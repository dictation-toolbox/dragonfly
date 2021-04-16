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

import collections, types

from .dictation                 import AlternativeDictation, DefaultDictation, UserDictation
from ..base                     import CompilerBase, CompilerError
from ...grammar                 import elements as elements_

from kaldi_active_grammar import WFST, KaldiRule
from kaldi_active_grammar import Compiler as KaldiAGCompiler

import six
from six import text_type
from six.moves import map, range


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

    def __init__(self, model_dir, tmp_dir, auto_add_to_user_lexicon=None, lazy_compilation=None, **kwargs):
        CompilerBase.__init__(self)
        KaldiAGCompiler.__init__(self, model_dir=model_dir, tmp_dir=tmp_dir, **kwargs)

        self.auto_add_to_user_lexicon = bool(auto_add_to_user_lexicon)
        self.lazy_compilation = bool(lazy_compilation)

        self.kaldi_rule_by_rule_dict = collections.OrderedDict()  # Rule -> KaldiRule
        # self._grammar_rule_states_dict = dict()  # FIXME: disabled!
        self.kaldi_rules_by_listreflist_dict = collections.defaultdict(set)  # Rule -> Set[KaldiRule]
        self.internal_grammar = InternalGrammar('!kaldi_engine_internal')

    impossible_word = property(lambda self: self._longest_word.lower())  # FIXME
    unknown_word = property(lambda self: self._oov_word)

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
        for old, new in six.iteritems(self.untranslation_dict):
            output = output.replace(old, new)
        return output

    def translate_words(self, words):
        # Unused
        if self.translation_dict:
            new_words = []
            for word in words:
                for old, new in six.iteritems(self.translation_dict):
                    word = word.replace(old, new)
                new_words.extend(word.split())
            words = new_words
        words = [word.lower() for word in words]
        for i in range(len(words)):
            if words[i] not in self.lexicon_words:
                words[i] = self.handle_oov_word(words[i])
        return words

    def handle_oov_word(self, word):
        if self.auto_add_to_user_lexicon:
            try:
                pronunciations = self.add_word(word, lazy_compilation=True)
            except Exception as e:
                self._log.exception("%s: exception automatically adding word %r" % (self, word))
            else:
                for phones in pronunciations:
                    self._log.warning("%s: Word not in lexicon (generated automatic pronunciation): %r [%s]" % (self, word, ' '.join(phones)))
                return word

        self._log.warning("%s: Word %r not in lexicon (will NOT be recognized; see documentation about user lexicon and auto_add_to_user_lexicon)" % (self, word))
        word = self.impossible_word
        return word

    #-----------------------------------------------------------------------
    # Methods for compiling grammars.

    def compile_grammar(self, grammar, engine):
        self._log.debug("%s: Compiling grammar %s." % (self, grammar.name))

        kaldi_rule_by_rule_dict = collections.OrderedDict()  # Rule -> KaldiRule
        for rule in grammar.rules:
            if rule.exported:
                if rule.element is None:
                    # We cannot deal with an empty rule (could be fixed by refactoring)
                    raise CompilerError("Invalid None element for %s in %s" % (rule, grammar))

                kaldi_rule = KaldiRule(self,
                    name='%s::%s' % (grammar.name, rule.name),
                    has_dictation=None)  # has_dictation is set to True during compilation below if that is the case
                kaldi_rule.parent_grammar = grammar
                kaldi_rule.parent_rule = rule
                kaldi_rule_by_rule_dict[rule] = kaldi_rule

                try:
                    self._compile_rule_root(rule, grammar, kaldi_rule)
                    kaldi_rule.has_dictation = bool(kaldi_rule.has_dictation)  # Convert None to False
                except Exception:
                    raise self.make_compiler_error_for_kaldi_rule(kaldi_rule)

        self.kaldi_rule_by_rule_dict.update(kaldi_rule_by_rule_dict)
        return kaldi_rule_by_rule_dict

    def _compile_rule_root(self, rule, grammar, kaldi_rule):
        src_state, dst_state = self._compile_rule(rule, grammar, kaldi_rule, kaldi_rule.fst, export=True)
        if kaldi_rule.fst.native and not kaldi_rule.fst.has_path():
            # Impossible paths break AGF compilation, so bolt on an Impossible element. This is less than ideal, but what are you doing compiling this anyway?
            self._compile_impossible(None, src_state, dst_state, grammar, kaldi_rule, kaldi_rule.fst)
        kaldi_rule.compile(lazy=self.lazy_compilation)

    def _compile_rule(self, rule, grammar, kaldi_rule, fst, export):
        """ :param export: whether rule is exported (a root rule) """
        # Determine whether this rule has already been compiled.
        # if (grammar.name, rule.name) in self._grammar_rule_states_dict:
        #     self._log.debug("%s: Already compiled rule %s%s." % (self, rule.name, ' [EXPORTED]' if export else ''))
        #     return self._grammar_rule_states_dict[(grammar.name, rule.name)]
        # else:
        self._log.debug("%s: Compiling rule %s%s." % (self, rule.name, ' [EXPORTED]' if export else ''))

        if export:
            # Root rule, so must handle grammar's weight, in addition to this rule's weight
            weight = self.get_weight(grammar) * self.get_weight(rule)
            outer_src_state = fst.add_state(initial=True)
            inner_src_state = fst.add_state()
            fst.add_arc(outer_src_state, inner_src_state, None, weight=weight)
            dst_state = fst.add_state(final=True)

        else:
            # Only handle this rule's weight
            weight = self.get_weight(rule)
            outer_src_state = fst.add_state()
            inner_src_state = fst.add_state()
            fst.add_arc(outer_src_state, inner_src_state, None, weight=weight)
            dst_state = fst.add_state()

        self.compile_element(rule.element, inner_src_state, dst_state, grammar, kaldi_rule, fst)
        # self._grammar_rule_states_dict[(grammar.name, rule.name)] = (src_state, dst_state)
        return (outer_src_state, dst_state)

    def unload_grammar(self, grammar, rules, engine):
        for rule in rules:
            kaldi_rule = self.kaldi_rule_by_rule_dict[rule]
            # Unload kaldi_rule: destroy() handles KaldiAGCompiler stuff; we must handle ours
            kaldi_rule.destroy()
            del self.kaldi_rule_by_rule_dict[rule]
            for kaldi_rules_set in self.kaldi_rules_by_listreflist_dict.values():
                kaldi_rules_set.discard(kaldi_rule)
            # NOTE: the kaldi_rule_by_rule_dict we returned from compile_grammar() is not updated, but it should be dropped upon unload anyway!

    def update_list(self, lst, grammar):
        # Note: we update all rules in all grammars that reference this list (unlike WSR/natlink?)
        lst_kaldi_rules = self.kaldi_rules_by_listreflist_dict[id(lst)]
        for kaldi_rule in lst_kaldi_rules:
            with kaldi_rule.reload():
                self._compile_rule_root(kaldi_rule.parent_rule, grammar, kaldi_rule)

    #-----------------------------------------------------------------------
    # Methods for compiling elements.

    _eps_like_nonterms = frozenset()  # Dictation is non-empty now ('#nonterm:dictation', '#nonterm:dictation_cloud')

    def compile_element(self, element, *args, **kwargs):
        """Compile element in FST (from src_state to dst_state) and return result."""
        # Look for a compiler method to handle the given element.
        for element_type, compiler in self.element_compilers:
            if isinstance(element, element_type):
                return compiler(self, element, *args, **kwargs)
        # Didn't find a compiler method for this element type.
        raise NotImplementedError("Compiler %s not implemented for element type %s." % (self, element))

    # @trace_compile
    def _compile_sequence(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        src_state = self.add_weight_linkage(src_state, dst_state, self.get_weight(element), fst)
        children = element.children
        # Optimize for special lengths
        if len(children) == 0:
            fst.add_arc(src_state, dst_state, None)
            return

        elif len(children) == 1:
            return self.compile_element(children[0], src_state, dst_state, grammar, kaldi_rule, fst)

        else:  # len(children) >= 2:
            # Handle Repetition elements differently as a special case
            is_repetition = isinstance(element, elements_.Repetition)
            if is_repetition and element.optimize:
                # Repetition...
                # Insert new states, so back arc only affects child
                s1 = fst.add_state()
                s2 = fst.add_state()
                fst.add_arc(src_state, s1, None)
                # NOTE: to avoid creating an un-decodable epsilon loop, we must not allow an all-epsilon child here (compile_graph_agf should check this)
                self.compile_element(children[0], s1, s2, grammar, kaldi_rule, fst)
                if not fst.has_eps_path(s1, s2, self._eps_like_nonterms):
                    fst.add_arc(s2, s1, fst.eps_disambig, fst.eps)  # Back arc, uses eps_disambig ('#0')
                    fst.add_arc(s2, dst_state, None)
                    return

                else:
                    # Cannot do optimize path, because of epsilon loop, so finish up with Sequence path
                    self._log.warning("%s: Cannot optimize Repetition element, because its child element can match empty string;"
                        " falling back to inefficient non-optimize path. (this is not that bad)" % self)
                    states = [src_state, s2] + [fst.add_state() for i in range(len(children)-2)] + [dst_state]
                    for i, child in enumerate(children[1:], start=1):
                        s1 = states[i]
                        s2 = states[i + 1]
                        self.compile_element(child, s1, s2, grammar, kaldi_rule, fst)
                    return

            else:
                # Sequence, not Repetition...
                # Insert new states for individual children elements
                states = [src_state] + [fst.add_state() for i in range(len(children)-1)] + [dst_state]
                for i, child in enumerate(children):
                    s1 = states[i]
                    s2 = states[i + 1]
                    self.compile_element(child, s1, s2, grammar, kaldi_rule, fst)
                return

    # @trace_compile
    def _compile_alternative(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        src_state = self.add_weight_linkage(src_state, dst_state, self.get_weight(element), fst)
        for child in element.children:
            self.compile_element(child, src_state, dst_state, grammar, kaldi_rule, fst)

    # @trace_compile
    def _compile_optional(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        src_state = self.add_weight_linkage(src_state, dst_state, self.get_weight(element), fst)
        self.compile_element(element.children[0], src_state, dst_state, grammar, kaldi_rule, fst)
        fst.add_arc(src_state, dst_state, None)

    # @trace_compile
    def _compile_literal(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        weight = self.get_weight(element)  # Handle weight internally below, without adding a state
        words = element.words
        words = list(map(text_type, words))
        # words = self.translate_words(words)

        # Special case optimize single-word literal
        if len(words) == 1:
            word = words[0].lower()
            if word not in self.lexicon_words:
                word = self.handle_oov_word(word)
            fst.add_arc(src_state, dst_state, word, weight=weight)

        else:
            words = [word.lower() for word in words]
            for i in range(len(words)):
                if words[i] not in self.lexicon_words:
                    words[i] = self.handle_oov_word(words[i])
            # "Insert" new states for individual words
            states = [src_state] + [fst.add_state() for i in range(len(words)-1)] + [dst_state]
            for i, word in enumerate(words):
                fst.add_arc(states[i], states[i + 1], word, weight=weight)
                weight = None  # Only need to set weight on first arc

    # @trace_compile
    def _compile_rule_ref(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        weight = self.get_weight(element)  # Handle weight internally below without adding a state
        # Compile target rule "inline"
        rule_src_state, rule_dst_state = self._compile_rule(element.rule, grammar, kaldi_rule, fst, export=False)
        fst.add_arc(src_state, rule_src_state, None, weight=weight)
        fst.add_arc(rule_dst_state, dst_state, None)

    # @trace_compile
    def _compile_list_ref(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        src_state = self.add_weight_linkage(src_state, dst_state, self.get_weight(element), fst)
        # list_rule_name = "__list_%s" % element.list.name
        if element.list not in grammar.lists:
            # Should only happen during initial compilation; during updates, we must skip this
            grammar.add_list(element.list)
        self.kaldi_rules_by_listreflist_dict[id(element.list)].add(kaldi_rule)
        for child_str in element.list.get_list_items():
            self._compile_literal(MockLiteral(child_str.split()), src_state, dst_state, grammar, kaldi_rule, fst)

    # @trace_compile
    def _compile_dictation(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        kaldi_rule.has_dictation = True
        src_state = self.add_weight_linkage(src_state, dst_state, self.get_weight(element), fst)
        # fst.add_arc(src_state, dst_state, '#nonterm:dictation', olabel=WFST.eps)
        extra_state = fst.add_state()
        cloud_dictation = isinstance(element, (AlternativeDictation, DefaultDictation)) and element.cloud
        dictation_nonterm = '#nonterm:dictation_cloud' if cloud_dictation else '#nonterm:dictation'
        fst.add_arc(src_state, extra_state, '#nonterm:dictation', dictation_nonterm)
        # Accepts zero or more words
        fst.add_arc(extra_state, dst_state, WFST.eps, '#nonterm:end')
        # fst.add_arc(extra_state, dst_state, '!SIL', '#nonterm:end')  # Causes problems with lack of phones during decoding

    # @trace_compile
    def _compile_impossible(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        # FIXME: not impossible enough (lower probability?)
        # Note: setting weight=0 breaks compilation!
        fst.add_arc(src_state, dst_state, self.impossible_word, weight=1e-10)

    # @trace_compile
    def _compile_empty(self, element, src_state, dst_state, grammar, kaldi_rule, fst):
        src_state = self.add_weight_linkage(src_state, dst_state, self.get_weight(element), fst)
        fst.add_arc(src_state, dst_state, WFST.eps)

    #-----------------------------------------------------------------------
    # Utility methods.

    def get_weight(self, obj, name='weight'):
        """ Gets the weight of given grammar or rule, checking for invalid values. """
        weight = getattr(obj, name, 1)
        if isinstance(obj, (elements_.Dictation, UserDictation)) and isinstance(weight, types.FunctionType):
            # Ignore crazy string method handling on Dictation elements; use default value
            weight = 1
        try:
            weight = float(weight)
        except TypeError:
            self._log.error("%s: Weight must be a numeric, but %s.%s is %s: %r" % (self, obj, name, type(weight), weight))
            weight = 1
        if weight <= 0:
            self._log.error("%s: Weight cannot be negative or 0, but %s.%s is %s" % (self, obj, name, weight))
            weight = 1e-9
        return weight

    def add_weight_linkage(self, outer_src_state, dst_state, weight, fst):
        """ Returns new source state, to be used by the caller as the effective source state. Only modifies if weight is non-default. """
        if (weight is None) or (weight == 1):
            return outer_src_state
        # self._log.debug("%s: Adding weight linkage for weight=%s" % (self, weight))
        inner_src_state = fst.add_state()
        fst.add_arc(outer_src_state, inner_src_state, None, weight=weight)
        return inner_src_state

    def make_compiler_error_for_kaldi_rule(self, kaldi_rule):
        message = "Exception while compiling %s in %s" % (kaldi_rule.parent_rule, kaldi_rule.parent_grammar)
        if six.PY2: self._log.exception("%s: %s", self, message)  # Imitate PY3's chained exceptions traceback
        rule_tree = kaldi_rule.parent_rule.element.element_tree_string()
        # Limit to at most 100 lines, unless debug logging enabled
        if not self._log.isEnabledFor(10) and rule_tree.count('\n') >= 10:
            rule_tree_lines = rule_tree.split('\n')[:10]
            rule_tree_lines.append("----8<----" * 7)
            rule_tree_lines.append("Printout truncated at 100 lines. To see all, run with:")
            rule_tree_lines.append("    logging.getLogger('kaldi.compiler').setLevel(logging.DEBUG)")
            rule_tree = '\n'.join(rule_tree_lines)
        self._log.error("Failed rule's elements:\n" + rule_tree)
        kaldi_rule.destroy()
        return CompilerError(message)

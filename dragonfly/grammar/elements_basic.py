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
    This file implements several fundamental grammar elements.
"""


import types
import dragonfly.log as log_
import rule as rule_
import list as list_
import wordinfo


#===========================================================================
# Element base class.

class ElementBase(object):

    name = "uninitialized"

    _log_decode = log_.get_log("grammar.decode")
    _log_eval = log_.get_log("grammar.eval")

    def __init__(self, actions=(), name=None):
        self._actions = self._copy_sequence(actions,
                                            "actions", ActionBase)
        self.name = name

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        if self.name:   name_str = ", name=%r" % self.name
        else:           name_str = ""
        return "%s(...%s)" % (self.__class__.__name__, name_str)

    def _get_children(self):
        return ()
    children = property(lambda self: self._get_children(),
                        doc="Read-only access to child elements.")

    def element_tree_string(self):
        indent = "  "
        tree = []
        stack = [(self, 0)]
        while stack:
            element, index = stack.pop()
            if index == 0:
                tree.append((element, len(stack)))
            if len(element.children) > index:
                stack.append((element, index + 1))
                stack.append((element.children[index], 0))
        lines = (indent*depth + str(element) for element, depth in tree)
        return "\n".join(lines)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_dependencies(self):
        return []

    def i_compile(self, compiler):
        raise NotImplementedError("Call to virtual method i_compile()"
                                  " in base class ElementBase")

    def i_gstring(self):
        raise NotImplementedError("Call to virtual method i_gstring()"
                                  " in base class ElementBase")

    def add_action(self, action):
        assert isinstance(action, ActionBase)
        self._actions = self._actions + (action,)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        raise NotImplementedError("Call to virtual method i_decode()"
                                  " in base class ElementBase")

    def i_evaluate(self, node, data):
        if self._log_eval: self._log_eval.debug( \
            "%s%s: evaluating %s" % ("  "*node.depth, self, node.words()))

        # First, evaluate all this element's children.
        [c.actor.i_evaluate(c, data) for c in node.children]

        # Second, evaluate this element's actions.
        self._evaluate_actions(self._actions, node, data)

    def _evaluate_actions(self, actions, node, data):
        [a.evaluate(node, data) for a in actions]

    def value(self, node):
        return node.words()

    #-----------------------------------------------------------------------
    # Internal utility methods for use by derived classes.

    def _copy_sequence(self, sequence, name, item_types=None):
        """\
            Check that a given object is a sequence, copy its contents
            into a new tuple, and check that each item is of a given type.
        """
        try:
            result = tuple(sequence)
        except TypeError:
            raise TypeError("%s object must be a sequence." % name)

        if not item_types: return result

        invalid = [c for c in result if not isinstance(c, item_types)]
        if invalid:
            raise TypeError("%s object must contain only %s types.  (Received %s)" \
                            % (name, item_types, result))
        return result


#===========================================================================
# Basic structural element classes.

class Sequence(ElementBase):

    def __init__(self, children=(), actions=(), name=None):
        ElementBase.__init__(self, actions, name=name)
        self._children = self._copy_sequence(children,
                                             "children", ElementBase)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_dependencies(self):
        dependencies = []
        for c in self._children:
            dependencies.extend(c.i_dependencies())
        return dependencies

    def i_compile(self, compiler):
        if len(self._children) > 1:
            compiler.start_sequence()
            [c.i_compile(compiler) for c in self._children]
            compiler.end_sequence()
        elif len(self._children) == 1:
            self._children[0].i_compile(compiler)

    def i_gstring(self):
        return "(" \
             + " ".join(map(lambda e: e.i_gstring(), self._children)) \
             + ")"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # Special case for an empty sequence.
        if len(self._children) == 0:
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_failure(self)
            return

        # Attempt to walk a path through the entire sequence of children
        #  so that each one decodes successfully.
        path = [self._children[0].i_decode(state)]
        while path:
            # Allow the last child to attempt decoding.
            try: path[-1].next()
            except StopIteration:
                # Last child failed to decode, remove from path to
                #  allowed the one-before-last child to reattempt.
                path.pop()
            else:
                # Last child successfully decoded.
                if len(path) < len(self._children):
                    # Sequence not yet complete, append the next child.
                    path.append(self._children[len(path)].i_decode(state))
                else:
                    # Sequence complete, all children decoded successfully.
                    state.decode_success(self)
                    yield state
                    state.decode_retry(self)

        # Sequence of children could not all decode successfully: failure.
        state.decode_failure(self)
        return


#---------------------------------------------------------------------------

class Optional(ElementBase):

    def __init__(self, child, actions=(), name=None):
        ElementBase.__init__(self, actions, name)

        if not isinstance(child, ElementBase):
            raise TypeError("Child of %s object must be an"
                            " ElementBase instance." % self)
        self._child = child
        self._greedy = True

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        return (self._child, )

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_dependencies(self):
        return self._child.i_dependencies()

    def i_compile(self, compiler):
        compiler.start_optional()
        self._child.i_compile(compiler)
        compiler.end_optional()

    def i_gstring(self):
        return "[" + self._child.i_gstring() + "]"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # If in greedy mode, allow the child to decode before.
        if self._greedy:
            for result in self._child.i_decode(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

            # Rollback decoding so that the null-decode can be yielded.
            state.decode_rollback(self)

        # Yield the null-decode possibility.
        state.decode_success(self)
        yield state
        state.decode_retry(self)

        # If not in greedy mode, allow the child to decode after.
        if not self._greedy:
            for result in self._child.i_decode(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

        # No more decoding possibilities available, failure.
        state.decode_failure(self)
        return

#---------------------------------------------------------------------------

class Alternative(ElementBase):

    def __init__(self, children=(), actions=(), name=None):
        ElementBase.__init__(self, actions, name)
        self._children = self._copy_sequence(children,
                                             "children", ElementBase)

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def _get_children(self):
        return self._children

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_gstring(self):
        return "(" \
             + " | ".join(map(lambda e: e.i_gstring(), self._children)) \
             + ")"

    def i_dependencies(self):
        dependencies = []
        for c in self._children:
            dependencies.extend(c.i_dependencies())
        return dependencies

    def i_compile(self, compiler):
        if len(self._children) > 1:
            compiler.start_alternative()
            [c.i_compile(compiler) for c in self._children]
            compiler.end_alternative()
        elif len(self._children) == 1:
            self._children[0].i_compile(compiler)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # Special case for an empty list of alternatives.
        if len(self._children) == 0:
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_failure(self)
            return

        # Iterate through the children.
        for child in self._children:

            # Iterate through this child's possible decoding states.
            for result in child.i_decode(state):
                state.decode_success(self)
                yield state
                state.decode_retry(self)

            # Rollback to the alternative's original state, so that the
            #  next child starts decoding without interference from the
            #  previous child.
            state.decode_rollback(self)

        # None of the children could decode successfully: failure.
        state.decode_failure(self)
        return

    def value(self, node):
        return node.children[0].value()


#---------------------------------------------------------------------------

class Repetition(Sequence):

    def __init__(self, child, min=1, max=None, actions=(), name=None):
        if not isinstance(child, ElementBase):
            raise TypeError("Child of %s object must be an"
                            " ElementBase instance." % self)
        assert isinstance(min, int)
        assert max is None or isinstance(max, int)
        assert max is None or min < max

        self._child = child
        self._min = min
        if max is None: self._max = min + 1
        else:           self._max = max

        optional_length = self._max - self._min - 1
        if optional_length > 0:
            element = Optional(child)
            for index in xrange(optional_length):
                element = Optional(Sequence([child, element]))

            if self._min >= 1:
                children = [child] * self._min + [element]
            else:
                children = [element]
        elif self._min > 0:
            children = [child] * self._min
        else:
            raise ValueError("Repetition not allowed to be empty.")

        Sequence.__init__(self, children, actions, name=name)

    def i_dependencies(self):
        return self._child.i_dependencies()

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def get_repetitions(self, node):
        repetitions = []
        for index in xrange(self._min):
            element = node.children[index]
            if element.actor != self._child:
                raise TypeError("Invalid child of %s: %s" \
                    % (self, element.actor))
            repetitions.append(element)

        if self._max - self._min > 1:
            optional = node.children[-1]
            while optional.children:
                child = optional.children[0]
                if isinstance(child.actor, Sequence):
                    assert len(child.children) == 2
                    element, optional = child.children
                    if element.actor != self._child:
                        raise TypeError("Invalid child of %s: %s" \
                            % (self, element.actor))
                    repetitions.append(element)
                elif child.actor == self._child:
                    repetitions.append(child)
                    break
                else:
                    raise TypeError("Invalid child of %s: %s" \
                        % (self, child.actor))

        return repetitions


#---------------------------------------------------------------------------

class Literal(ElementBase):

    def __init__(self, text, actions=(), name=None, value=None):
        ElementBase.__init__(self, actions, name)
        self._value = value

        if not isinstance(text, (str, unicode)):
            raise TypeError("Text of %s object must be a"
                            " string." % self)
        self._words = text.split()

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return "%s('%s')" % (self.__class__.__name__, " ".join(self._words))

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_compile(self, compiler):
        if len(self._words) == 1:
            compiler.add_word(self._words[0])
        elif len(self._words) > 1:
            compiler.start_sequence()
            [compiler.add_word(w) for w in self._words]
            compiler.end_sequence()

    def i_gstring(self):
        return " ".join(self._words)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # Iterate through this element's words.
        # If all match, success.  Else, failure.
        for i in xrange(len(self._words)):
            if state.word(i) != self._words[i]:
                state.decode_failure(self)
                return

        # All words matched, success.
        state.next(len(self._words))
        state.decode_success(self)
        yield state
        state.decode_retry(self)

        # Only one decoding possibility, failure on retry.
        state.decode_failure(self)
        return

    def value(self, node):
        if self._value is None: return " ".join(node.words())
        else: return self._value

#---------------------------------------------------------------------------

class Rule(ElementBase):

    def __init__(self, rule, actions=(), name=None):
        ElementBase.__init__(self, actions, name)

        if not isinstance(rule, rule_.Rule):
            raise TypeError("Rule object of %s object must be a"
                            " Dragonfly rule." % self)
        self._rule = rule

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        if not hasattr(self, "_rule"):
            return ElementBase.__str__(self)
        return '%s(%s)' % (self.__class__.__name__, self._rule.name)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_dependencies(self):
        return [self._rule]

    def i_compile(self, compiler):
        compiler.add_rule(self._rule.name, imported=False)

    def i_gstring(self):
        return "<" + self._rule.name + ">"


    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # Allow the rule to attempt decoding.
        for result in self._rule.i_decode(state):
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        # The rule failed to deliver a valid decoding, failure.
        state.decode_failure(self)
        return

#---------------------------------------------------------------------------

class List(ElementBase):

    def __init__(self, list, key=None, actions=(), name=None):
        ElementBase.__init__(self, actions, name)

        if not isinstance(list, list_.ListBase):
            raise TypeError("List object of %s object must be a"
                            " Dragonfly list." % self)
        self._list = list
        self._key = key

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        arguments = self._list.name
        if self._key: arguments += ", key=%r" % self._key
        return '%s(%s)' % (self.__class__.__name__, arguments)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_dependencies(self):
        return [self._list]

    def i_compile(self, compiler):
        compiler.add_list(self._list.name)

    def i_gstring(self):
        return "{" + self._list.name + "}"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # If the next word is in the list, success.
        if state.word() in self._list:
            state.next()
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        # If the word is not in the list, or on retry, failure.
        state.decode_failure(self)
        return

    def i_evaluate(self, node, data):
        if self._log_eval: self._log_eval.debug( \
            "%s%s: evaluating %s" % ("  "*node.depth, self, node.words()))

        # If a key was set, store the matched words in the data dictionary.
        if self._key:
            words = node.words()
            if len(words) != 1: raise ValueError("Decoding stack broken,"
                        " received multiple list words: %r." % words)
            data[self._key] = words[0]

        # Finally, evaluate this element's actions.
        self._evaluate_actions(self._actions, node, data)

#---------------------------------------------------------------------------

class DictList(List):

    def __init__(self, dict, key=None, actions=(), name=None):
        if not isinstance(dict, list_.DictList):
            raise TypeError("Dict object of %s object must be a"
                            " Dragonfly DictList." % self)
        List.__init__(self, dict, key, actions, name)

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_evaluate(self, node, data):
        if self._log_eval: self._log_eval.debug( \
            "%s%s: evaluating %s" % ("  "*node.depth, self, node.words()))

        # If a key was set, store the matched words in the data dictionary.
        if self._key:
            words = node.words()
            if len(words) != 1: raise ValueError("Decoding stack broken,"
                        " received multiple list words: %r." % words)
            data[self._key] = self._list[words[0]]

        # Finally, evaluate this element's actions.
        self._evaluate_actions(self._actions, node, data)

#---------------------------------------------------------------------------

class Empty(ElementBase):

    def __init__(self, actions=(), name=None):
        ElementBase.__init__(self, actions, name)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_compile(self, compiler):
        pass

    def i_gstring(self):
        return ""

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        state.decode_success(self)
        yield state
        state.decode_retry(self)

        state.decode_failure(self)
        return


#===========================================================================
# Slightly more complex element classes.

class Dictation(ElementBase):

    _rule_name = "dgndictation"

    def __init__(self, name=None, format=True, actions=()):
        ElementBase.__init__(self, actions, name)
        self._format_words = format

    def __str__(self):
        if self.name:
            return "%s(%r)" % (self.__class__.__name__, self.name)
        else:
            return "%s()" % (self.__class__.__name__)

    #-----------------------------------------------------------------------
    # Methods for load-time setup.

    def i_compile(self, compiler):
        compiler.add_rule(self._rule_name, imported=True)

    def i_gstring(self):
        return "<" + self._rule_name + ">"

    #-----------------------------------------------------------------------
    # Methods for runtime recognition processing.

    def i_decode(self, state):
        state.decode_attempt(self)

        # Check that at least one word has been dictated, otherwise feel.
        if state.rule() != "dgndictation":
            state.decode_failure(self)
            return

        # Determine how many words have been dictated.
        count = 1
        while state.rule(count) == self._rule_name:
            count += 1

        # Yield possible states where the number of dictated words
        # gobbled is decreased by 1 between yields.
        for i in xrange(count, 0, -1):
            state.next(i)
            state.decode_success(self)
            yield state
            state.decode_retry(self)
            state.decode_rollback(self)

        # None of the possible states were accepted, failure.
        state.decode_failure(self)
        return

    def i_evaluate(self, node, data):
        if self._log_eval: self._log_eval.debug( \
            "%s%s: evaluating %s" % ("  "*node.depth, self, node.words()))

        # If a name was set, store the matched words in the data dictionary.
        if self.name:
            if self._format_words:
                formatter = wordinfo.FormatState()
                data[self.name] = formatter.format_words(node.words())
                if self._log_eval: self._log_eval.debug( \
                    "%s%s: formatted '%s'" \
                     % ("  "*node.depth, self, data[self.name]))
            else:
                data[self.name] = node.words()

        # Finally, evaluate this element's actions.
        self._evaluate_actions(self._actions, node, data)

    def value(self, node):
        if self._format_words:
            formatter = wordinfo.FormatState()
            return formatter.format_words(node.words())
        else:
            return node.words()


#---------------------------------------------------------------------------

class LiteralChoice(Alternative):

    def __init__(self, name, choices, actions=()):

        # Build children elements with appropriate Insert actions.
        assert isinstance(choices, dict)
        self.choices = choices
        children = []
        for k, v in choices.items():
            action = Insert(name, v)
            child = Literal(k, actions=(action,))
            children.append(child)

        # Initialize super class.
        Alternative.__init__(self, children=children, actions=actions,
            name=name)

    def value(self, node):
        word = node.words()[0]
        return self.choices[word]


#===========================================================================
# Action classes can be used during element evaluation.

class ActionBase(object):

    def __init__(self):
        self._argstr = ""

    def _set_argstr(self, *args):
        self._argstr = ", ".join(map(str, args))

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._argstr)

    def evaluate(self, node, data):
        raise NotImplementedError("Call to virtual method evaluate()"
                                    " in base class ActionBase")


class Insert(ActionBase):

    def __init__(self, key, value):
        ActionBase.__init__(self)
        self._set_argstr(key, value)
        self.key = key; self.value = value

    def evaluate(self, node, data):
        data[self.key] = self.value


class Rename(ActionBase):

    def __init__(self, old_key, new_key):
        ActionBase.__init__(self)
        self._set_argstr(old_key, new_key)
        self.new_key = new_key
        self.old_key = old_key

    def evaluate(self, node, data):
        if self.old_key in data:
            data[self.new_key] = data.pop(self.old_key)


class Words(ActionBase):

    def __init__(self, key):
        ActionBase.__init__(self)
        self._set_argstr(key)
        self.key = key

    def evaluate(self, node, data):
        data[self.key] = " ".join(node.words())


class WordsMap(ActionBase):

    def __init__(self, key, dictionary):
        ActionBase.__init__(self)
        self._set_argstr(key, dictionary)
        self.key = key
        self.dictionary = dictionary

    def evaluate(self, node, data):
        words = " ".join(node.words())
        if words in self.dictionary:
            data[self.key] = self.dictionary[words]


class Func(ActionBase):

    def __init__(self, function):
        ActionBase.__init__(self)
        self.function = function

    def evaluate(self, node, data):
        self.function(node, data)
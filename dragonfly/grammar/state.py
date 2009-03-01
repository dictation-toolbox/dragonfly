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
    This file implements the State class, a utility
    class used during recognition decoding.
"""


from ..log          import get_log
from .grammar_base  import Grammar, GrammarError
from .rule_base     import Rule


class State(object):

    _log_decode = get_log("grammar.decode")

    #-----------------------------------------------------------------------
    # Methods for initialization.

    def __init__(self, results, rule_names, engine):
        self._results = results
        self._rule_names = rule_names
        self._engine = engine
        self._index = 0
        self._data = {}
        self._depth = 0
        self._stack = []
        self.initialize_decoding()

    def __str__(self):
        words = self.words()
        before = words[:self._index]
        after = words[self._index:]
        return " ".join(before) + " >> " + " ".join(after)

    #-----------------------------------------------------------------------
    # Methods for accessing recognition content.

    def word(self, delta = 0):
        i = self._index + delta
        if 0 <= i < len(self._results):
            return self._results[i][0]
        else:
            return None

    def rule(self, delta = 0):
        i = self._index + delta
        if 0 <= i < len(self._results):
            rule_id = self._results[i][1]
            if 0 <= rule_id < len(self._rule_names):
                return self._rule_names[rule_id]
            elif rule_id == 1000000:
                return "dgndictation"
            else:
                raise GrammarError("Malformed recognition data.")
        else:
            return None

    def word_rule(self, delta = 0):
        i = self._index + delta
        if 0 <= i < len(self._results):
            return self._results[i][0:2]
        else:
            return None

    def words(self, begin = 0, end = None):
        return [w[0] for w in self._results[begin:end]]

    def next(self, delta = 1):
        self._index += delta

    def finished(self):
        return self._index >= len(self._results)

    #-----------------------------------------------------------------------
    # Methods for tracking decoding of recognition.

    class _Frame(object):
        __slots__ = ("depth", "actor", "begin", "end")
        def __init__(self, depth, actor, begin):
            self.depth = depth; self.actor = actor
            self.begin = begin; self.end = None

    def initialize_decoding(self):
        self._depth = 0
        self._stack = []
        self._previous_index = None

    def decode_attempt(self, element):
        self._depth += 1
        self._stack.append(State._Frame(self._depth, element, self._index))
        self._log_step(element, "attempt")

    def decode_retry(self, element):
        frame = self._get_frame_from_actor(element)
        self._depth = frame.depth
        self._log_step(element, "retry")

    def decode_rollback(self, element):
        frame = self._get_frame_from_depth()
        if not frame or frame.actor != element:
            raise GrammarError("Recognition decoding stack broken")
        if frame is self._stack[-1]:
            # Last parser on the stack, rollback.
            self._index = frame.begin
        else:
            raise GrammarError("Recognition decoding stack broken")
        self._log_step(element, "rollback")

    def decode_success(self, element):
        self._log_step(element, "success")
        frame = self._get_frame_from_depth()
        if not frame or frame.actor != element:
            raise GrammarError("Recognition decoding stack broken.")
        frame.end = self._index
        self._depth -= 1

    def decode_failure(self, element):
        frame = self._stack.pop()
        self._index = frame.begin
        self._depth = frame.depth
        self._log_step(element, "failure")
        self._depth -= 1

    def _get_frame_from_depth(self):
        for i in xrange(len(self._stack)-1, -1, -1):
            frame = self._stack[i]
            if frame.depth == self._depth:
                return frame
        return None

    def _get_frame_from_actor(self, actor):
        for i in xrange(len(self._stack)-1, -1, -1):
            frame = self._stack[i]
            if frame.actor is actor:
                return frame
        return None

    def _log_step(self, parser, message):
        if not self._log_decode: return
        indent = "   " * self._depth
        output = "%s%s: %s" % (indent, message, parser)
        self._log_decode.debug(output)
        if self._index != self._previous_index:
            self._previous_index = self._index
            output = "%s -- Decoding State: '%s'" % (indent, str(self))
            self._log_decode.debug(output)

    #-----------------------------------------------------------------------
    # Methods for evaluation.

    def build_parse_tree(self):

        root = None
        node = None
        for frame in self._stack:
            while node and node.depth >= frame.depth:
                node = node.parent
            parent = node
            node = Node(parent, frame.actor, self._results,
                        frame.begin, frame.end, frame.depth, self._engine)
            if parent: parent.children.append(node)
            else: root = node

        return root


#---------------------------------------------------------------------------

class Node(object):

    __slots__ = ("parent", "children", "actor", "results",
                 "begin", "end", "depth", "engine")

    def __init__(self, parent, actor, results, begin, end, depth, engine):
        self.parent = parent; self.actor = actor; self.results = results
        self.begin = begin; self.end = end; self.depth = depth
        self.engine = engine
        self.children = []

    def __str__(self):
        return "Node: %s, %s" % (self.actor, self.words())

    def words(self):
        return [w[0] for w in self.results[self.begin:self.end]]

    def full_results(self):
        return self.results[self.begin:self.end]

    def value(self):
        try:
            return self.actor.value(self)
        except:
            pass

    def pretty_string(self, indent = ""):
        if not self.children:
            return "%s%s -> %r" % (indent, str(self), self.value())
        else:
            return "%s%s -> %r\n" % (indent, str(self), self.value()) \
                + "\n".join([n  .pretty_string(indent + "  ") \
                    for n in self.children])

    def _get_name(self):
        return self.actor.name
    name = property(_get_name)

    def has_child_with_name(self, name):
        """True if at least one node below this node has the given name."""
        for child in self.children:
            if child.name == name: return True
            if child.has_child_with_name(name): return True
        return False

    def get_child_by_name(self, name, shallow=False):
        """Get one node below this node with the given name."""
        for child in self.children:
            if child.name:
                if child.name == name:
                    return child
                if shallow:
                    # If shallow, don't look past named children.
                    continue
            match = child.get_child_by_name(name, shallow)
            if match: return match
        return None

    def get_children_by_name(self, name, shallow=False):
        """Get all nodes below this node with the given name."""
        matches = []
        for child in self.children:
            if child.name:
                if child.name == name:
                    matches.append(child)
                if shallow:
                    # If shallow, don't look past named children.
                    continue
            matches.extend(child.get_children_by_name(name, shallow))
        return matches

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
    This file implements the Grammar class, a grammar type representing
    a natlink grammar.
"""


try:
	import natlink
	import natlinkutils
except ImportError:
	natlink = None
	natlinkutils = None


# The trailing underscore in imported module names allows the original
# module names to be used conveniently for local variables.
# Done systematically, this leads to less confusion for readers of this
# source code.
#
import dragonfly.log as log_


class GrammarError(Exception):
    pass


class Grammar(object):

    _log_load = log_.get_log("grammar.load")
    _log_begin = log_.get_log("grammar.begin")
    _log_results = log_.get_log("grammar.results")


    def __init__(self, name, description=None, context=None):
        self._name = name
        self._description = description
        assert isinstance(context, context_.Context) or context is None
        self._context = context

        self._rules = []
        self._lists = []
        self._rule_names = None
        self._loaded = False
        self._enabled = True
        self._in_context = False
        self._engine = engine_.get_engine()

    def __del__(self):
        self.unload()

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    name = property(lambda self: self._name,
                    doc="Read-only access to name attribute.")

    rules = property(lambda self: self._rules,
                     doc="Read-only access to rules attribute.")

    lists = property(lambda self: self._lists,
                     doc="Read-only access to lists attribute.")

    loaded = property(lambda self: self._loaded,
                      doc = "Whether a grammar is loaded into natlink or not.")

    def enable(self):
        """Enable this grammar so that it is active to receive recognitions."""
        self._enabled = True

    def disable(self):
        """Disable this grammar so that it is not active to receive recognitions."""
        self._enabled = False

    enabled = property(lambda self: self._enabled,
                doc = "Whether a grammar is active to receive"
                      " recognitions or not.")

    def _set_engine(self, engine):
        if self._loaded:
            raise GrammarError(" Grammar %s: Cannot set engine while loaded."
                               % self)
        self._engine = engine
    engine = property(lambda self: self._engine, _set_engine,
                        doc="Property access to engine attribute.")

    #-----------------------------------------------------------------------
    # Methods for populating a grammar object instance.

    def add_rule(self, rule):
        """Add a rule to this grammar."""
        self._log_load.debug("Grammar %s: adding rule %s."
                            % (self._name, rule.name))

        # Check for correct type and duplicate rules or rule names.
        if self._loaded:
            raise GrammarError("Cannot add rule while loaded.")
        elif not isinstance(rule, rule_.Rule):
            raise GrammarError("Invalid rule object: %s" % rule)
        elif rule in self._rules:
            return
        elif rule.imported:
            return
        elif [True for r in self._rules if r.name == rule.name]:
            raise GrammarError("Two rules with the same name '%s' not"
                "allowed." % rule.name)

        # Append the rule to this grammar object's internal list.
        self._rules.append(rule)
        rule.grammar = self

    def add_list(self, lst):
        """Add a list to this grammar."""
        self._log_load.debug("Grammar %s: adding list %s."
                            % (self._name, lst.name))

        # Check for correct type and duplicate lists or list names.
        if self._loaded:
            raise GrammarError("Cannot add list while loaded.")
        elif not isinstance(lst, list_.ListBase):
            raise GrammarError("Invalid list object: %s" % lst)
        elif lst in self._lists:
            return
        elif [True for l in self._lists if l.name == lst.name]:
            raise GrammarError("Two lists with the same name '%s' not"
                "allowed." % lst.name)

        # Append the list to this grammar object's internal list.
        self._lists.append(lst)
        lst.grammar = self

    def add_dependency(self, dep):
        if isinstance(dep, rule_.Rule):
            self.add_rule(dep)
        elif isinstance(dep, list_.ListBase):
            self.add_list(dep)
        else: raise GrammarError("Unknown dependency type %s." % dep)

    #-----------------------------------------------------------------------
    # Methods for runtime modification of a grammar's contents.

    def activate_rule(self, rule):
        """Activate a rule loaded in this grammar."""
        self._log_load.debug("Grammar %s: activating rule %s." \
                            % (self._name, rule.name))

        # Check for correct type and valid rule instance.
        assert self._loaded
        assert isinstance(rule, rule_.Rule), \
            "Dragonfly rule objects must be of the type dragonfly.rule.Rule"
        if rule not in self._rules:
            raise GrammarError("Rule '%s' not loaded in this grammar." \
                % rule.name)

        # Activate the given rule.
        self._engine.activate_rule(rule, self)

    def deactivate_rule(self, rule):
        """Deactivate a rule loaded in this grammar."""
        self._log_load.debug("Grammar %s: deactivating rule %s." \
                            % (self._name, rule.name))

        # Check for correct type and valid rule instance.
        assert self._loaded
        assert isinstance(rule, rule_.Rule), \
            "Dragonfly rule objects must be of the type dragonfly.rule.Rule"
        if rule not in self._rules:
            raise GrammarError("Rule '%s' not loaded in this grammar." \
                % rule.name)

        # Deactivate the given rule.
        self._engine.deactivate_rule(rule, self)

    def update_list(self, lst):
        """Update a list loaded in this grammar."""
        self._log_load.debug("Grammar %s: updating list %s." \
                            % (self._name, lst.name))

        # Check for correct type and valid list instance.
#        assert self._loaded
        if lst not in self._lists:
            raise GrammarError("List '%s' not loaded in this grammar." \
                % lst.name)
        elif [True for w in lst.get_list_items()
                    if not isinstance(w, (str, unicode))]:
            raise GrammarError("List '%s' contains objects other than" \
                "strings." % lst.name)

        self._engine.update_list(lst, self)

    #-----------------------------------------------------------------------
    # Methods for registering a grammar object instance in natlink.

    def load(self):
        """Load this grammar into natlink."""

        # Prevent loading the same grammar multiple times.
        if self._loaded: return
        self._log_load.debug("Grammar %s: loading." % self._name)

        self._engine.load_grammar(self)
        self._loaded = True

        # Update all lists loaded in this grammar.
        for lst in self._lists:
            lst._update()

    def unload(self):
        """Unload this grammar from natlink."""

        # Prevent unloading the same grammar multiple times.
        if not self._loaded: return
        self._log_load.debug("Grammar %s: unloading." % self._name)

        self._engine.unload_grammar(self)

    #-----------------------------------------------------------------------
    # Callback methods for handling utterances and recognitions.

    def process_begin(self, executable, title, handle):

        self._log_begin.debug("Grammar %s: detected beginning of utterance."
                              % self._name)
        self._log_begin.debug("Grammar %s:     executable '%s', title '%s'."
                              % (self._name, executable, title))

        if not self._enabled:
            # Grammar is disabled, so deactivate all active rules.
            [r.deactivate() for r in self._rules if r.active]

        elif not self._context \
                or self._context.matches(executable, title, handle):
            # Grammar is within context.
            if not self._in_context:
                self._in_context = True
                self.enter_context()
            self._process_begin(executable, title, handle)
            for r in self._rules:
                if r.exported and hasattr(r, "process_begin"):
                    r.process_begin(executable, title, handle)

        else:
            # Grammar's context doesn't match, deactivate active rules.
            if self._in_context:
                self._in_context = False
                self.exit_context()
            [r.deactivate() for r in self._rules if r.active]

        self._log_begin.debug("Grammar %s:     active rules: %s."
            % (self._name, [r.name for r in self._rules if r.active]))

    def enter_context(self):
        pass

    def exit_context(self):
        pass

    def _process_begin(self, executable, title, handle):
        pass


# The trailing underscore in imported module names allows the original
# module names to be used conveniently for local variables.
# Done systematically, this leads to less confusion for readers of this
# source code.
#
import state as state_
import rule as rule_
import list as list_
import compiler as compiler_
import context as context_
import dragonfly.engines.engine as engine_

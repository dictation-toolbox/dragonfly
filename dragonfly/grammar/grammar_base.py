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
Grammar class
============================================================================

"""

import logging
from six import string_types

from ..engines         import get_engine
from .rule_base        import Rule
from .list             import ListBase
from .context          import Context
from ..error           import GrammarError


# --------------------------------------------------------------------------

class Grammar(object):
    """
        Grammar class for managing a set of rules.

        This base grammar class takes care of the communication
        between Dragonfly's object model and the backend speech
        recognition engine.  This includes compiling rules and
        elements, loading them, activating and deactivating
        them, and unloading them.  It may, depending on the
        engine, also include receiving recognition results and
        dispatching them to the appropriate rule.

         - *name* -- name of this grammar
         - *description* (str, default: None) --
           description for this grammar
         - *context* (Context, default: None) --
           context within which to be active.  If *None*, the grammar will
           always be active.

    """

    # pylint: disable=too-many-instance-attributes
    _log_load     = logging.getLogger("grammar.load")
    _log_begin    = logging.getLogger("grammar.begin")
    _log_results  = logging.getLogger("grammar.results")
    _log          = logging.getLogger("grammar")

    # ----------------------------------------------------------------------
    # Methods for initialization and cleanup.

    def __init__(self, name, description=None, context=None, engine=None):
        self._name = name
        self._description = description
        if not (isinstance(context, Context) or context is None):
            raise TypeError("context must be either a Context object or "
                            "None")
        self._context = context

        if engine:
            self._engine = engine
        else:
            self._engine = get_engine()

        self._rules = []
        self._lists = []
        self._rule_names = None
        self._loaded = False
        self._enabled = True
        self._in_context = False

    def __del__(self):
        try:
            if self._loaded:
                return
            self.unload()
        except Exception as e:
            try:
                self._log.exception("Exception during grammar unloading:"
                                    " %s", e)
            except Exception as e:
                pass

    # ----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    name = property(lambda self: self._name,
                    doc="A grammar's name.")

    rules = property(lambda self: tuple(self._rules),
                     doc="List of a grammar's rules.")

    active_rules = property(
        lambda self: [r for r in self.rules if r.active],
        doc="List of a grammar's active rules."
    )

    lists = property(lambda self: tuple(self._lists),
                     doc="List of a grammar's lists.")

    loaded = property(lambda self: self._loaded,
                      doc="Whether a grammar is loaded into"
                          " its SR engine or not.")

    @property
    def rule_names(self):
        """
        List of grammar's rule names.
        """
        result = []
        for rule in self._rules:
            result.append(rule.name)
        return result

    def enable(self):
        """
            Enable this grammar so that it is active to receive
            recognitions.

        """
        self._enabled = True

    def disable(self):
        """
            Disable this grammar so that it is not active to
            receive recognitions.

        """
        self._enabled = False

    enabled = property(lambda self: self._enabled,
                       doc="Whether a grammar is active to receive "
                           "recognitions or not.")

    def set_exclusiveness(self, exclusive):
        """ Set the exclusiveness of this grammar. """
        self._engine.set_exclusiveness(self, exclusive)

    def set_exclusive(self, exclusive):
        """ Alias of :meth:`set_exclusiveness`. """
        self.set_exclusiveness(exclusive)

    def _set_engine(self, engine):
        if self._loaded:
            raise GrammarError(" Grammar %s: Cannot set engine while "
                               "loaded." % self)
        self._engine = engine

    engine = property(lambda self: self._engine, _set_engine,
                      doc="A grammar's SR engine.")

    def set_context(self, context):
        """
            Set the context for this grammar, under which it and its rules
            will be active and receive recognitions if it is also enabled.

            Use of this method overwrites any previous context.

            Contexts can be modified at any time, but will only be checked
            when :meth:`process_begin` is called.

            :param context: context within which to be active.  If *None*,
                the grammar will always be active.
            :type context: Context|None
        """
        if not (isinstance(context, Context) or context is None):
            raise TypeError("context must be either a Context object or "
                            "None")
        self._context = context

    context = property(lambda self: self._context,
                       doc="A grammar's context, under which it and its "
                           "rules will be active and receive recognitions "
                           "if it is also enabled.")

    # ----------------------------------------------------------------------
    # Methods for populating a grammar object instance.

    def add_rule(self, rule):
        """
        Add a rule to this grammar.

        The following rules apply when adding rules into grammars:

        #. Rules **cannot** be added to grammars that are currently loaded.
        #. Two or more rules with the same name are **not** allowed.

        .. warning::

           Note that while adding the same ``Rule`` object to more than one
           grammar is allowed, it is **not** recommended! This is because
           the context and active/enabled states of these rules will not
           function correctly if used. It is better to use *separate*
           ``Rule`` instances for each grammar instead.

        :param rule: Dragonfly rule
        :type rule: Rule
        """
        self._log_load.debug("Grammar %s: adding rule %s.",
                             self._name, rule.name)

        # Check for correct type and duplicate rules or rule names.
        if self._loaded:
            raise GrammarError("Cannot add rule while loaded.")
        elif not isinstance(rule, Rule):
            raise GrammarError("Invalid rule object: %s" % rule)
        elif rule in self._rules:
            return
        elif rule.imported:
            return
        elif [True for r in self._rules if r.name == rule.name]:
            raise GrammarError("Two rules with the same name '%s' not"
                               " allowed." % rule.name)
        elif rule.grammar is not None and rule.exported:
            self._log_load.warning("Exported rule %s is already in grammar "
                                   "%s, adding it to grammar %s is not "
                                   "recommended.", rule.name,
                                   rule.grammar.name, self._name)

        # Append the rule to this grammar object's internal list.
        self._rules.append(rule)
        rule.grammar = self

    def remove_rule(self, rule):
        """
        Remove a rule from this grammar.

        Rules **cannot** be removed from grammars that are currently loaded.

        :param rule: Dragonfly rule
        :type rule: Rule
        """
        self._log_load.debug("Grammar %s: removing rule %s.",
                             self._name, rule.name)

        # Check for correct type.
        if self._loaded:
            raise GrammarError("Cannot remove rule while loaded.")
        elif not isinstance(rule, Rule):
            raise GrammarError("Invalid rule object: %s" % rule)
        elif rule not in self._rules:
            return

        # Remove the rule from this grammar object's internal list.
        self._rules.remove(rule)
        rule.grammar = None

    def add_list(self, lst):
        """
        Add a list to this grammar.

        Lists **cannot** be added to grammars that are currently loaded.

        :param lst: Dragonfly list
        :type lst: ListBase
        """
        self._log_load.debug("Grammar %s: adding list %s.",
                             self._name, lst.name)

        # Make sure that the list can be loaded and is not a duplicate.
        if self._loaded:
            raise GrammarError("Cannot add list while loaded.")
        elif not isinstance(lst, ListBase):
            raise GrammarError("Invalid list object: %s" % lst)

        for l in self._lists:
            if l.name == lst.name:
                if l is lst:
                    # This list was already added previously, so ignore.
                    return
                raise GrammarError("Two lists with the same name '%s' not"
                                   " allowed." % lst.name)

        # Append the list to this grammar object's internal list.
        self._lists.append(lst)
        lst.grammar = self

    def remove_list(self, lst):
        """
        Remove a list from this grammar.

        Lists **cannot** be removed from grammars that are currently loaded.

        :param lst: Dragonfly list
        :type lst: ListBase
        """
        self._log_load.debug("Grammar %s: removing list %s.",
                             self._name, lst.name)

        # Check for correct type.
        if self._loaded:
            raise GrammarError("Cannot remove list while loaded.")
        elif not isinstance(lst, ListBase):
            raise GrammarError("Invalid list object: %s" % lst)
        elif lst.name not in [l.name for l in self._lists]:
            return

        # Remove the list from this grammar object's internal list.
        self._lists.remove(lst)
        lst.grammar = None

    def add_dependency(self, dep):
        """
            Add a rule or list dependency to this grammar.

            **Internal:** this method is normally *not* called
            by the user, but instead automatically during
            grammar compilation.

        """
        if isinstance(dep, Rule):
            self.add_rule(dep)
        elif isinstance(dep, ListBase):
            self.add_list(dep)
        else:
            raise GrammarError("Unknown dependency type %s." % dep)

    def add_all_dependencies(self):
        """
            Iterate through the grammar's rules and add all the necessary dependencies.

            **Internal** This method is called when the grammar is loaded.
        """
        memo = set()
        for r in self._rules:
            for d in r.dependencies(memo):
                self.add_dependency(d)

    # ----------------------------------------------------------------------
    # Methods for runtime modification of a grammar's contents.

    def activate_rule(self, rule):
        """
            Activate a rule loaded in this grammar.

            **Internal:** this method is normally *not* called
            directly by the user, but instead automatically when
            the rule itself is activated by the user.

        """
        self._log_load.debug("Grammar %s: activating rule %s.",
                             self._name, rule.name)

        # Check for correct type and valid rule instance.
        assert self._loaded
        assert isinstance(rule, Rule), \
            "Dragonfly rule objects must be of the type dragonfly.rule.Rule"
        if rule not in self._rules:
            raise GrammarError("Rule '%s' not loaded in this grammar."
                               % rule.name)
        if not rule.exported:
            return

        # Activate the given rule.
        self._engine.activate_rule(rule, self)

    def deactivate_rule(self, rule):
        """
            Deactivate a rule loaded in this grammar.

            **Internal:** this method is normally *not* called
            directly by the user, but instead automatically when
            the rule itself is deactivated by the user.

        """
        self._log_load.debug("Grammar %s: deactivating rule %s.",
                             self._name, rule.name)

        # Check for correct type and valid rule instance.
        assert self._loaded
        assert isinstance(rule, Rule), \
            "Dragonfly rule objects must be of the type dragonfly.rule.Rule"
        if rule not in self._rules:
            raise GrammarError("Rule '%s' not loaded in this grammar."
                               % rule.name)
        if not rule.exported:
            return

        # Deactivate the given rule.
        self._engine.deactivate_rule(rule, self)

    def update_list(self, lst):
        """
            Update a list's content loaded in this grammar.

            **Internal:** this method is normally *not* called
            directly by the user, but instead automatically when
            the list itself is modified by the user.

        """
        self._log_load.debug("Grammar %s: updating list %s.",
                             self._name, lst.name)

        # Check for correct type and valid list instance.
        #        assert self._loaded
        if lst not in self._lists:
            raise GrammarError("List '%s' not loaded in this grammar."
                               % lst.name)
        elif [True for w in lst.get_list_items()
              if not isinstance(w, string_types)]:
            raise GrammarError("List '%s' contains objects other than"
                               "strings." % lst.name)

        self._engine.update_list(lst, self)

    # ----------------------------------------------------------------------
    # Methods for registering a grammar object instance in natlink.

    def load(self):
        """ Load this grammar into its SR engine. """

        self._log_load.debug("Grammar %s: loading into engine %s.",
                             self._name, self._engine)

        # Prevent loading the same grammar multiple times.
        if self._loaded:
            return

        self.add_all_dependencies()
        self._engine.load_grammar(self)
        self._loaded = True
        self._in_context = False

        # Update all rules loaded in this grammar.
        for rule in self._rules:
            # Explicitly compare to False so that uninitialized rules (which
            # have active set to None) are activated.
            if rule.active is not False:
                rule.activate(force=True)
        # Update all lists loaded in this grammar.
        for lst in self._lists:
            # pylint: disable=protected-access
            lst._update()

        #        self._log_load.warning(self.get_complexity_string())

    def unload(self):
        """ Unload this grammar from its SR engine. """

        # Prevent unloading the same grammar multiple times.
        if not self._loaded:
            return
        self._log_load.debug("Grammar %s: unloading.", self._name)

        self._engine.unload_grammar(self)
        self._loaded = False
        self._in_context = False

    def get_complexity_string(self):
        """
            Build and return a human-readable text giving insight into the
            complexity of this grammar.

        """
        rules_all = self.rules
        rules_top = [r for r in self.rules if r.exported]
        rules_imp = [r for r in self.rules if r.imported]
        elements = []
        for rule in rules_all:
            elements.extend(self._get_element_list(rule))
        text = ("Grammar: %3d (%3d, %3d) rules, %4d elements (%3d avg)     %s"
                % (
                    len(rules_all), len(rules_top), len(rules_imp),
                    len(elements), len(elements) / len(rules_all),
                    self,
                )
                )
        for rule in rules_all:
            elements = self._get_element_list(rule)
            text += "\n  Rule: %4d  %s" % (len(elements), rule)
        return text

    def _get_element_list(self, thing):
        if isinstance(thing, Rule):
            element = thing.element
        else:
            element = thing
        elements = [element]
        for child in element.children:
            elements.extend(self._get_element_list(child))
        return elements

    # ----------------------------------------------------------------------
    # Callback methods for handling utterances and recognitions.

    def process_begin(self, executable, title, handle):
        """
            Start of phrase callback.

            *Usually derived grammar classes override
            ``Grammar._process_begin`` instead of this method, because
            this method merely wraps that method adding context matching.*

            This method is called when the speech recognition
            engine detects that the user has begun to speak a
            phrase.

            Arguments:
             - *executable* -- the full path to the module whose
               window is currently in the foreground.
             - *title* -- window title of the foreground window.
             - *handle* -- window handle to the foreground window.

        """
        # pylint: disable=expression-not-assigned

        self._log_begin.debug("Grammar %s: detected beginning of "
                              "utterance.", self._name)
        self._log_begin.debug("Grammar %s: executable '%s', title '%s'.",
                              self._name, executable, title)

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

        self._log_begin.debug("Grammar %s:     active rules: %s.",
                              self._name,
                              [r.name for r in self._rules if r.active])

    def enter_context(self):
        """
            Enter context callback.

            This method is called when a phrase-start has been
            detected.  It is only called if this grammar's
            context previously did not match but now does
            match positively.

        """

    def exit_context(self):
        """
            Exit context callback.

            This method is called when a phrase-start has been
            detected.  It is only called if this grammar's
            context previously did match but now doesn't
            match positively anymore.

        """

    def _process_begin(self, executable, title, handle):
        """
            Start of phrase callback.

            *This usually is the method which should be overridden
            to give derived grammar classes custom behavior.*

            This method is called when the speech recognition
            engine detects that the user has begun to speak a
            phrase. This method is called by the
            ``Grammar.process_begin`` method only if this
            grammar's context matches positively.

            Arguments:
             - *executable* -- the full path to the module whose
               window is currently in the foreground.
             - *title* -- window title of the foreground window.
             - *handle* -- window handle to the foreground window.

        """

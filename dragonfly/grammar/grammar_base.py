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
    This file implements the Grammar class.

"""

from ..log             import get_log
from ..engines.engine  import get_engine
from .rule_base        import Rule
from .list             import ListBase
from .context          import Context


#---------------------------------------------------------------------------

class GrammarError(Exception):
    pass


#---------------------------------------------------------------------------

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

    _log_load     = get_log("grammar.load")
    _log_begin    = get_log("grammar.begin")
    _log_results  = get_log("grammar.results")
    _log          = get_log("grammar")


    #-----------------------------------------------------------------------
    # Methods for initialization and cleanup.

    def __init__(self, name, description=None, context=None):
        self._name = name
        self._description = description
        assert isinstance(context, Context) or context is None
        self._context = context

        self._rules = []
        self._lists = []
        self._rule_names = None
        self._loaded = False
        self._enabled = True
        self._in_context = False
        self._engine = get_engine()

    def __del__(self):
        try:
            self.unload()
        except Exception, e:
            pass

    #-----------------------------------------------------------------------
    # Methods for runtime introspection.

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    name = property(lambda self: self._name,
                    doc="A grammar's name.")

    rules = property(lambda self: tuple(self._rules),
                     doc="List of a grammar's rules.")

    lists = property(lambda self: tuple(self._lists),
                     doc="List of a grammar's lists.")

    loaded = property(lambda self: self._loaded,
                      doc="Whether a grammar is loaded into"
                          " its SR engine or not.")

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
                doc = "Whether a grammar is active to receive"
                      " recognitions or not.")

    def _set_engine(self, engine):
        if self._loaded:
            raise GrammarError(" Grammar %s: Cannot set engine while loaded."
                               % self)
        self._engine = engine
    engine = property(lambda self: self._engine, _set_engine,
                        doc="A grammar's SR engine.")

    #-----------------------------------------------------------------------
    # Methods for populating a grammar object instance.

    def add_rule(self, rule):
        """ Add a rule to this grammar. """
        self._log_load.debug("Grammar %s: adding rule %s."
                            % (self._name, rule.name))

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
                "allowed." % rule.name)

        # Append the rule to this grammar object's internal list.
        self._rules.append(rule)
        rule.grammar = self

    def remove_rule(self, rule):
        """ Remove a rule from this grammar. """
        self._log_load.debug("Grammar %s: removing rule %s."
                            % (self._name, rule.name))

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
        """ Add a list to this grammar. """
        self._log_load.debug("Grammar %s: adding list %s."
                            % (self._name, lst.name))

        # Check for correct type and duplicate lists or list names.
        if self._loaded:
            raise GrammarError("Cannot add list while loaded.")
        elif not isinstance(lst, ListBase):
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
        else: raise GrammarError("Unknown dependency type %s." % dep)

    #-----------------------------------------------------------------------
    # Methods for runtime modification of a grammar's contents.

    def activate_rule(self, rule):
        """
            Activate a rule loaded in this grammar.

            **Internal:** this method is normally *not* called 
            directly by the user, but instead automatically when 
            the rule itself is activated by the user.

        """
        self._log_load.debug("Grammar %s: activating rule %s." \
                            % (self._name, rule.name))

        # Check for correct type and valid rule instance.
        assert self._loaded
        assert isinstance(rule, Rule), \
            "Dragonfly rule objects must be of the type dragonfly.rule.Rule"
        if rule not in self._rules:
            raise GrammarError("Rule '%s' not loaded in this grammar." \
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
        self._log_load.debug("Grammar %s: deactivating rule %s." \
                            % (self._name, rule.name))

        # Check for correct type and valid rule instance.
        assert self._loaded
        assert isinstance(rule, Rule), \
            "Dragonfly rule objects must be of the type dragonfly.rule.Rule"
        if rule not in self._rules:
            raise GrammarError("Rule '%s' not loaded in this grammar." \
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
        """ Load this grammar into its SR engine. """

        # Prevent loading the same grammar multiple times.
        if self._loaded: return
        self._log_load.debug("Grammar %s: loading." % self._name)

        self._engine.load_grammar(self)
        self._loaded = True
        self._in_context = False

        # Update all lists loaded in this grammar.
        for rule in self._rules:
            if rule.active != False:
                rule.activate()
        # Update all lists loaded in this grammar.
        for lst in self._lists:
            lst._update()

    def unload(self):
        """ Unload this grammar from its SR engine. """

        # Prevent unloading the same grammar multiple times.
        if not self._loaded: return
        self._log_load.debug("Grammar %s: unloading." % self._name)

        self._engine.unload_grammar(self)
        self._loaded = False
        self._in_context = False

    #-----------------------------------------------------------------------
    # Callback methods for handling utterances and recognitions.

    def process_begin(self, executable, title, handle):
        """
            Start of phrase callback.

            This method is called when the speech recognition 
            engine detects that the user has begun to speak a 
            phrase.

            Arguments:
             - *executable* -- the full path to the module whose 
               window is currently in the foreground.
             - *title* -- window title of the foreground window.
             - *handle* -- window handle to the foreground window.

        """
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
        """
            Enter context callback.

            This method is called when a phrase-start has been 
            detected.  It is only called if this grammar's 
            context previously did not match but now does
            match positively.

        """
        pass

    def exit_context(self):
        """
            Exit context callback.

            This method is called when a phrase-start has been 
            detected.  It is only called if this grammar's 
            context previously did match but now doesn't 
            match positively anymore.

        """
        pass

    def _process_begin(self, executable, title, handle):
        """
            Start of phrase callback.

            *This usually the method which should be overridden 
            to give derived grammar classes custom behavior.*

            This method is called when the speech recognition 
            engine detects that the user has begun to speak a 
            phrase.  This method is only called when this 
            grammar's context does match positively.  It is 
            called by the ``Grammar.process_begin`` method.

            Arguments:
             - *executable* -- the full path to the module whose 
               window is currently in the foreground.
             - *title* -- window title of the foreground window.
             - *handle* -- window handle to the foreground window.

        """
        pass

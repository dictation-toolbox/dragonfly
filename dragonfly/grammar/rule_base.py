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
Rule class
============================================================================

"""

from ..log import get_log
from .context import Context


class Rule(object):
    """
        Rule class for implementing complete or partial voice-commands.

        This rule class represents a voice-command or part of a voice-
        command.  It contains a root element, which defines the language 
        construct of this rule.

        Constructor arguments:
         - *name* (*str*) -- name of this rule.  If *None*, a unique
           name will automatically be generated.
         - *element* (*Element*) --
           root element for this rule
         - *context* (*Context*, default: *None*) --
           context within which to be active.  If *None*, the rule will
           always be active when its grammar is active.
         - *imported* (boolean, default: *False*) --
           if true, this rule is imported from outside its grammar
         - *exported* (boolean, default: *False*) --
           if true, this rule is a complete top-level rule which can be
           spoken by the user.  This should be *True* for voice-commands
           that the user can speak.

        The *self._log* logger objects should be used in methods of 
        derived classes for logging purposes.  It is a standard logger 
        object from the *logger* module in the Python standard library.

    """

    _log_load   = get_log("grammar.load")
    _log_eval   = get_log("grammar.eval")
    _log_proc   = get_log("grammar.process")
    _log        = get_log("rule")
    _log_begin  = get_log("rule")

    # Counter ID used for anonymous rules to give them a unique name.
    _next_anonymous_id = 0

    def __init__(self, name=None, element=None, context=None,
                 imported=False, exported=False):
        # The default argument for *element* is NOT acceptable; this
        #  construction is used for backwards compatibility and argument
        #  order.
        self._element = element
        self._imported = imported
        self._exported = exported

        # Generate a unique name for this rule if none is given.
        if not name:
            name = "_anonrule_%03d_%s" % (Rule._next_anonymous_id,
                                          self.__class__.__name__)
            Rule._next_anonymous_id += 1
        self._name = name

        self._active = None
        self._enabled = True
        assert isinstance(context, Context) or context is None
        self._context = context
        self._grammar = None

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    #-----------------------------------------------------------------------
    # Protected attribute access.

    name     = property(lambda self: self._name,
                        doc="This rule's name.  (Read-only)")
    element  = property(lambda self: self._element,
                        doc="This rule's root element.  (Read-only)")
    exported = property(lambda self: self._exported,
                        doc="This rule's exported status.  (Read-only)")
    imported = property(lambda self: self._imported,
                        doc="This rule's imported status.  (Read-only)")

    def enable(self):
        """
            Enable this grammar so that it is active to receive 
            recognitions.

        """
        self._enabled = True
        self.activate()

    def disable(self):
        """
            Disable this grammar so that it is not active to 
            receive recognitions.

        """
        self._enabled = False
        if self._active:
            self.deactivate()

    enabled = property(lambda self: self._enabled,
                doc = "Whether a grammar is active to receive"
                      " recognitions or not.")

    def _get_grammar(self):
        return self._grammar
    def _set_grammar(self, grammar):
        if self._grammar is None:
            self._grammar = grammar
        elif grammar is None:
            self._grammar = None
        elif grammar != self._grammar:
            raise TypeError("The grammar object a Dragonfly rule"
                " cannot be changed after it has been set (%s != %s)."
                % (grammar, self._grammar))
    grammar = property(_get_grammar, _set_grammar,
                       doc="This rule's grammar object.  (Set once)")

    #-----------------------------------------------------------------------
    # Internal methods for controlling a rules active state.

    def process_begin(self, executable, title, handle):
        """
            Start of phrase callback.

            This method is called when the speech recognition 
            engine detects that the user has begun to speak a 
            phrase.  It is called by the rule's containing grammar
            if the grammar and this rule are active.

            The default implementation of this method checks
            whether this rule's context matches, and if it does
            this method calls
            :meth:`._process_begin`.

            Arguments:
             - *executable* -- the full path to the module whose 
               window is currently in the foreground
             - *title* -- window title of the foreground window
             - *handle* -- window handle to the foreground window

        """
        assert self._grammar
        if not self._enabled:
            if self._active:
                self.deactivate()
            return
        if self._context:
            if self._context.matches(executable, title, handle):
                if not self._active:
                    self.activate()
                self._process_begin()
            else:
                if self._active:
                    self.deactivate()
        else:
            if not self._active:
                self.activate()
            self._process_begin()

    def activate(self):
        if not self._grammar:
            raise TypeError("A Dragonfly rule cannot be activated"
                            " before it is bound to a grammar.")
        if not self._enabled:
            if self._active:
                self.deactivate()
            return
        if not self._active:
            self._grammar.activate_rule(self)
            self._active = True

    def deactivate(self):
        if not self._grammar:
            raise TypeError("A Dragonfly rule cannot be deactivated"
                            " before it is bound to a grammar.")
        if self._active:
            try:
                self._grammar.deactivate_rule(self)
            except Exception, e:
                self._log.warning("Failed to deactivate rule: %s (%s)"
                                  % (self, e))
            self._active = False

    active = property(lambda self: self._active,
        doc="Read-only access to a rule's active state.")

    exported = property(lambda self: self._exported,
        doc="Read-only access to a rule's exported state.")

    #-----------------------------------------------------------------------
    # Compilation related methods.

    def gstring(self):
        s = "<" + self.name + ">"
        if self.imported: return s + " imported;"
        if self.exported: s += " exported"
        s += " = " + self.element.gstring() + ";"
        return s

    def dependencies(self):
        if self._element:
            return self._element.dependencies()
        else:
            return []

    #-----------------------------------------------------------------------
    # Methods for decoding and evaluating recognitions.

    def decode(self, state):
        state.decode_attempt(self)

        for result in self._element.decode(state):
            state.decode_success(self)
            yield state
            state.decode_retry(self)

        state.decode_failure(self)
        return

    def value(self, node):
        """
            Start of phrase callback.

            This method is called to obtain the semantic value associated 
            with a particular recognition.  It could be called from 
            another rule's :meth:`.value` if 
            that rule references this rule.  If also be called from this 
            rule's :meth:`.process_recognition`
            if that method has been overridden to do so in a derived
            class.

            The default implementation of this method returns the value of 
            this rule's root element.

            .. note::

               This is generally the method which developers should 
               override in derived rule classes to change the default
               semantic value of a recognized rule.

        """
        return node.children[0].value()

    #-----------------------------------------------------------------------
    # Methods for processing before-and-after utterances.

    def _process_begin(self):
        """
            Start of phrase detection callback.

            This method is called when the speech recognition 
            engine detects that the user has begun to speak a 
            phrase.  It is called by this rule's
            :meth:`.process_begin`
            after some context checks.

            The default implementation of this method does nothing.

            .. note::

               This is generally the method which developers should
               override in derived rule classes to give them custom
               functionality when the start of a phrase is detected.

        """
        pass

    def process_results(self, data):
        pass

    def process_recognition(self, node):
        """
            Rule recognition callback.

            This method is called when the user has spoken words matching 
            this rule's contents.  This method is called only once for 
            each recognition, and only for the matching top-level rule.

            The default implementation of this method does nothing.

            .. note::

               This is generally the method which developers should
               override in derived rule classes to give them custom
               functionality when a top-level rule is recognized.

        """
        pass


class ImportedRule(Rule):

    def __init__(self, name):
        self._name = name
        self._imported = True
        self._exported = False
        self._active = False
        self._grammar = None

    #-----------------------------------------------------------------------
    # Compilation related methods.

    def dependencies(self):
        return ()

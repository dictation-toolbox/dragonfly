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
EngineBase class
============================================================================

"""

import logging
from .timer import Timer

import dragonfly.engines


#---------------------------------------------------------------------------

class EngineError(Exception):
    pass

class MimicFailure(EngineError):
    pass


#---------------------------------------------------------------------------

class EngineContext(object):

    def __init__(self, engine):
        self._engine = engine

    def __enter__(self):
        self._engine.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._engine.disconnect()


#---------------------------------------------------------------------------

class EngineBase(object):
    """ Base class for engine-specific back-ends. """

    _log = logging.getLogger("engine")
    _name = "base"
    _timer_manager = None

    #-----------------------------------------------------------------------

    def __init__(self):
        # Register initialization of this engine.
        dragonfly.engines.register_engine_init(self)

        self._grammar_wrappers = {}
        self._recognition_observer_manager = None

#    def __del__(self):
#        try:
#            try:
#                self.disconnect()
#            except Exception, e:
#                self._log.exception("Engine destructor raised an exception: %s" % e)
#        except:
#            pass

    def __str__(self):
        return "%s()" % self.__class__.__name__

    @property
    def name(self):
        """ The human-readable name of this engine. """
        return self._name

    @property
    def grammars(self):
        """ Grammars loaded into this engine. """
        # Return a list of each GrammarWrapper's Grammar object.
        return list(map(
            lambda w: w.grammar,
            self._grammar_wrappers.values()
        ))

    def connect(self):
        """ Connect to back-end SR engine. """
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    def disconnect(self):
        """ Disconnect from back-end SR engine. """
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    def connection(self):
        """ Context manager for a connection to the back-end SR engine. """
        return EngineContext(self)

    #-----------------------------------------------------------------------
    # Methods for administrating grammar wrappers.

    def create_timer(self, callback, interval):
        return Timer(callback, interval, self._timer_manager)

    #-----------------------------------------------------------------------
    # Methods for administrating grammar wrappers.

    def _build_grammar_wrapper(self, grammar):
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    #-----------------------------------------------------------------------
    # Methods for working with grammars.

    def load_grammar(self, grammar):
        wrapper_key = id(grammar)
        if wrapper_key in self._grammar_wrappers:
            self._log.warning("Grammar %s loaded multiple times." % grammar)
            return

        wrapper = self._load_grammar(grammar)
        self._grammar_wrappers[wrapper_key] = wrapper

    def _load_grammar(self, grammar):
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    def unload_grammar(self, grammar):
        wrapper_key = id(grammar)
        if wrapper_key not in self._grammar_wrappers:
            raise EngineError("Grammar %s cannot be unloaded because"
                              " it was never loaded." % grammar)
        wrapper = self._grammar_wrappers.pop(wrapper_key)
        self._unload_grammar(grammar, wrapper)

    def _unload_grammar(self, grammar, wrapper):
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    def update_list(self, lst, grammar):
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    def set_exclusiveness(self, grammar, exclusive):
        raise NotImplementedError("Virtual method not implemented for"
                                  " engine %s." % self)

    def _get_grammar_wrapper(self, grammar):
        wrapper_key = id(grammar)
        if wrapper_key not in self._grammar_wrappers:
            raise EngineError("Grammar %s never loaded." % grammar)
        wrapper = self._grammar_wrappers[wrapper_key]
        return wrapper

    #-----------------------------------------------------------------------
    # Recognition observer methods.

    def register_recognition_observer(self, observer):
        self._recognition_observer_manager.register(observer)

    def unregister_recognition_observer(self, observer):
        self._recognition_observer_manager.unregister(observer)

    def enable_recognition_observers(self):
        self._recognition_observer_manager.enable()

    def disable_recognition_observers(self):
        self._recognition_observer_manager.disable()


    #-----------------------------------------------------------------------
    #  Miscellaneous methods.

    def mimic(self, words):
        """ Mimic a recognition of the given *words*. """
        raise NotImplementedError("Engine %s not implemented." % self)

    def speak(self, text):
        """ Speak the given *text* using text-to-speech. """
        raise NotImplementedError("Engine %s not implemented." % self)

    @property
    def language(self):
        """
        Current user language of the SR engine. (Read-only)

        :rtype: str
        """
        return self._get_language()

    def _get_language(self):
        raise NotImplementedError("Engine %s not implemented." % self)

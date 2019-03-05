#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# (c) Copyright 2018 by David Williams-King
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
VoxhubEngine class
============================================================================

"""

import logging

from dragonfly.engines.backend_voxhub import is_engine_available
from compiler import VoxhubCompiler
from ..base import EngineBase, EngineError, MimicFailure
from .dictation import VoxhubDictationContainer
from mic import setup
from multiprocessing import Process, Queue
from ...grammar.state import State
import re


class VoxhubEngine(EngineBase):
    """Speech recognition engine back-end for Kaldi-based Voxhub.io."""

    _log = logging.getLogger("engine.voxhub")
    _name = ".voxhub"
    _timer_manager = None
    DictationContainer = VoxhubDictationContainer

    def __init__(self):
        self._connected = False
        self._queue = None
        self._process = None
        EngineBase.__init__(self)

    def __str__(self):
        return "%s()" % self.__class__.__name__

    def connect(self):
        """ Connect to back-end SR engine. """
        self._queue = Queue()
        self._process = Process(target=setup, args=("silvius-server.voxhub.io", self._queue,))
        self._process.start()
        # self._ws_connection = setup("silvius-server.voxhub.io")
        self._connected = True
        # raise NotImplementedError("Virtual method not implemented for"
        #                           " engine %s." % self)

    def disconnect(self):
        """ Disconnect from back-end SR engine. """
        if self._process:
            self._process.terminate()
            self._connected = False
            print "Connection closed"
        self._connected = False
        # raise NotImplementedError("Virtual method not implemented for"
        #                           " engine %s." % self)

    def connection(self):
        """ Context manager for a connection to the back-end SR engine. """
        return EngineContext(self)

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
        print "[LOAD]", grammar

        """ Load the given *grammar* and return a wrapper. """
        self._log.debug("Engine %s: loading grammar %s."
                        % (self, grammar.name))

        grammar.engine = self
        # Dependency checking.
        memo = []
        for r in grammar.rules:
            for d in r.dependencies(memo):
                grammar.add_dependency(d)

        wrapper = self._build_grammar_wrapper(grammar)
        self.set_grammar(wrapper)
        return wrapper

    def _build_grammar_wrapper(self, grammar):
        return grammar

    def set_grammar(self, wrapper):
        self._set_grammar(wrapper)

    def _set_grammar(self, wrapper):
        self._current_grammar_wrapper = wrapper

        # Return if the engine isn't available or if wrapper is None.
        if not (is_engine_available() and wrapper):
            return

        self.compiler = VoxhubCompiler()
        self.compiler.compile_grammar(wrapper)  # extract grammar

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

    def activate_grammar(self, grammar):
        print("Activating grammar %s." % grammar.name)
        grammar.enable()

    def deactivate_grammar(self, grammar):
        print("Deactivating grammar %s." % grammar.name)
        grammar.disable()

    def activate_rule(self, rule, grammar):
        print("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        self._log.debug("Activating rule %s in grammar %s." % (rule.name, grammar.name))
        #wrapper = self._get_grammar_wrapper(grammar)
        #if not wrapper:
        #    return
        #try:
        #    wrapper.dictation_grammar.enable_rule(rule.name)
        #    self.unset_search(wrapper.search_name)
        #    self.set_grammar(wrapper)
        #except UnknownWordError as e:
        #    self._log.error(e)
        #except Exception as e:
        #    self._log.exception("Failed to activate grammar %s: %s."
        #                        % (grammar, e))

    def deactivate_rule(self, rule, grammar):
        self._log.debug("Deactivating rule %s in grammar %s." % (rule.name, grammar.name))
        #wrapper = self._get_grammar_wrapper(grammar)
        #if not wrapper:
        #    return
        #try:
        #    wrapper.dictation_grammar.disable_rule(rule.name)
        #    self.unset_search(wrapper.search_name)
        #    self.set_grammar(wrapper)
        #except UnknownWordError as e:
        #    self._log.error(e)
        #except Exception as e:
        #    self._log.exception("Failed to activate grammar %s: %s."
        #                        % (grammar, e))

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
        print "[MIMIC]" + words

    def speak(self, text):
        print "[SPEAK]" + words

    def _get_language(self):
        return "en"  # default to english

    def process_transcript(self, transcript):
        results = [(word, 0) for word in transcript.split()]
        for (_, grammar) in self._grammar_wrappers.items():
            if self.process_results_with_grammar(results, ["dgndictation"], grammar):
                return True
        return False

    def process_results_with_grammar(self, results, rule_set, grammar):
        func = getattr(grammar, "process_recognition", None)
        if func:
            words = [w for w, r in results]
            if not func(words):
                return False

        s = State(results, rule_set, self)
        for r in grammar._rules:
            if not r.active or not r.exported: continue
            s.initialize_decoding()
            for result in r.decode(s):
                if s.finished():
                    self._log.debug("Matching rule: %s" % r.name)
                    root = s.build_parse_tree()
                    r.process_recognition(root)
                    return True
        return False

    def process_speech(self):
        while self._connected:
            result = self._queue.get()
            if result:
                # result = "quit"
                print "IT WORKS"
                print result
                if re.match(r"\s*quit\s*", result, re.I):
                    print('Exiting..')
                    self.disconnect()
                    return False
                self.process_transcript(result)

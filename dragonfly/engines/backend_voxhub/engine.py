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
from server import connect_to_server
from multiprocessing import Process, Queue
from ...grammar.state import State
from config import *
import re


class VoxhubEngine(EngineBase):
    """Speech recognition engine back-end for Kaldi-based Voxhub.io."""

    _log = logging.getLogger("engine.voxhub")
    _name = ".voxhub"
    _timer_manager = None
    DictationContainer = VoxhubDictationContainer

    def __init__(self):
        self._connected = False
        # Shared queue between processes for voxhub server and dragonfly
        self._queue = None
        # Background process for the voxhub server
        self._process = None
        # For enabling/disabling processing of transcript
        self._pause_transcript_processing = False
        # Pre checking of config. Improve config handling later
        self.validate_config()
        EngineBase.__init__(self)

    def __str__(self):
        return "%s()" % self.__class__.__name__

    def connect(self):
        """ Connect to back-end Voxhub server. """
        self._queue = Queue()
        self._process = Process(target=connect_to_server, args=(self._queue,))
        self._process.start()
        self._connected = True
        self.process_speech()

    def disconnect(self):
        """ Disconnect from back-end Voxhub server. """
        if self._process:
            self._process.terminate()
            print "Connection closed"
        self._connected = False

    def connection(self):
        """ Context manager for a connection to the back-end Voxhub engine. """
        return EngineContext(self)

    @staticmethod
    def validate_config():
        connection_attributes = ["SERVER","PORT","CONTENT_TYPE","PATH"]
        not_preset = []
        for a_connection_attribute in connection_attributes:
            if a_connection_attribute not in globals():
                not_preset.append(a_connection_attribute)

        if "MISC_CONFIG" not in globals():
            not_preset.append("MISC_CONFIG completely missing")
        else:
            misc_attributes = ["device", "keep_going", "hypotheses", "audio_gate",
                               "byte_rate", "chunk"]
            for a_misc_attribute in misc_attributes:
                if a_misc_attribute not in MISC_CONFIG:
                    not_preset.append('MISC_CONFIG["'+a_misc_attribute+'"]')

        if not_preset:
            # Raise an error with the attributes that weren't set.
            not_preset.sort()
            raise EngineError("Invalid engine configuration. Please check backend_voxhub/config.py. The following "
                              "attributes were not present: %s"
                              % ", ".join(not_preset))


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
        print "[SPEAK]" + text

    def _get_language(self):
        return "en"  # default to english

    def process_transcript(self, transcript):
        # print "Processing transcript"
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
                print "Transcript: ", result

                if re.match(r"\s*"+QUIT_PHRASE+"\s*", result, re.I):
                    print('Exiting..')
                    self.disconnect()
                    return False

                elif re.match(r"\s*"+SLEEP_PHRASE+"\s*", result, re.I):
                    self._pause_transcript_processing = True
                    print("Sleeping...")

                if not self._pause_transcript_processing:
                    self.process_transcript(result)

                if re.match(r"\s*"+WAKE_UP_PHRASE+"\s*", result, re.I):
                    self._pause_transcript_processing = False
                    print("Waking up...")

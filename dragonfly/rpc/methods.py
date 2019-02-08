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
RPC methods
----------------------------------------------------------------------------

For RPC methods to work they must be decorated with :code:`@rpc_method`.
For example::

    from dragonfly.engines import get_engine
    from dragonfly.rpc import rpc_method

    @rpc_method
    def get_engine_language():
        return get_engine().language


Built-in RPC methods
============================================================================

"""

import logging
import threading
import time

from decorator import decorator
from six import string_types

from jsonrpc.dispatcher import Dispatcher

from .. import get_engine, CompoundRule, MappingRule
from ..engines.base import MimicFailure


# Set up a logger.
_log = logging.getLogger("rpc.methods")

# Initialise a JSON RPC method dispatcher.
dispatcher = Dispatcher()

# Set up some variables used in scheduling RPC methods to run via engine
# timers.
_request_queue = []
_results_map = {}
_lock = threading.RLock()

def _queue_not_empty():
    with _lock:  # len() is not atomic.
        return len(_request_queue) > 0


def server_timer_function():
    # This function is scheduled via 'engine.create_timer' by the RPC server
    # on start() and removed on stop().
    start_time = time.time()
    while _queue_not_empty():
        with _lock:
            # Unpack the first request and process it.
            condition, method, args, kwargs = _request_queue.pop(0)
        try:
            result = method(*args, **kwargs)
        except Exception as e:
            # Log any exceptions.
            _log.exception("Exception occurred during RPC method %s: %s"
                           % (method.__name__, e))
            result = e

        # Save the result return to the RPC client, using the memory
        # address of the condition as the key.
        with _lock:
            _results_map[id(condition)] = result

        # Notify the waiting thread about the result being ready.
        with condition:
            condition.notifyAll()

        # Return if this function has been running for more than 100 ms.
        # Processing will resume whenever the function is next scheduled
        # to run.
        if time.time() - start_time > 0.1:
            break


@decorator
def _execute_via_timer(method, *args, **kwargs):
    # Create a thread condition for waiting for the method's result.
    # These conditions use a separate lock from _lock.
    condition = threading.Condition()

    # Acquire _lock and append the request to the queue.
    with _lock:
        _request_queue.append((condition, method, args, kwargs))

    # Wait for the result.
    with condition:
        condition.wait()

    # Acquire _lock again and pop the method result.
    with _lock:
        result = _results_map.pop(id(condition))

    # Raise an error if it's an exception (json-rpc handles this),
    # otherwise return it.
    if isinstance(result, Exception):
        raise result
    else:
        return result


def rpc_method(method):
    return dispatcher.add_method(_execute_via_timer(method))


@rpc_method
def list_grammars():
    """
    Get a list of grammars loaded into the current engine.

    This includes grammar rules and attributes.
    """
    # Send rule and grammar data back to the client.
    grammars = []
    engine = get_engine()
    for grammar in engine.grammars:
        rules = []
        for rule in grammar.rules:
            if isinstance(rule, CompoundRule):
                specs = [rule.spec]
            elif isinstance(rule, MappingRule):
                specs = sorted(rule.specs)
            else:
                specs = [rule.element.gstring()]
            rules.append({
                "name": rule.name, "specs": specs,
                "exported": rule.exported, "active": rule.active
            })

        # Add grammar attributes to the grammars list.
        is_active = any([r.active for r in grammar.rules])
        grammars.append({"name": grammar.name, "rules": rules,
                         "enabled": grammar.enabled, "active": is_active})

    return grammars


@rpc_method
def mimic(words):
    """
    Mimic the given *words*.

    :param words: string or list of words to mimic
    :returns: whether the mimic was a success
    :rtype: bool
    """
    if isinstance(words, string_types):
        words = words.split()
    try:
        get_engine().mimic(words)
        return True
    except MimicFailure:
        return False


@rpc_method
def speak(text):
    """
    Speak the given *text* using text-to-speech using :meth:`engine.speak`.

    :param text: text to speak using text-to-speech
    :type text: str
    """
    if not isinstance(text, string_types):
        raise TypeError("text must be a string")

    return get_engine().speak(text)


@rpc_method
def get_engine_language():
    """
    Get the current engine's language.

    :returns: language code
    :rtype: str
    """
    return get_engine().language

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

from decorator import decorator
from six import string_types

from jsonrpc.dispatcher import Dispatcher

from .. import get_engine, CompoundRule, MappingRule
from ..engines.base import MimicFailure


# Set up a logger.
_log = logging.getLogger("rpc.methods")

# Initialise a JSON RPC method dispatcher.
dispatcher = Dispatcher()


@decorator
def _execute_via_timer(method, *args, **kwargs):
    # Create a thread condition for waiting for the method's result.
    condition = threading.Condition()

    closure = []
    def timer_func():
        try:
            closure.append(method(*args, **kwargs))
        except Exception as e:
            # Log any exceptions.
            _log.exception("Exception occurred during RPC method '%s': %s" %
                           (method.__name__, e))
            closure.append(e)

        # Notify the waiting thread that the result is ready.
        with condition:
            condition.notify()

    # Start a non-repeating timer to execute timer_func().
    get_engine().create_timer(timer_func, 0, repeating=False)

    # Wait for the result.
    with condition:
        condition.wait()

    # Raise an error if it's an exception (json-rpc handles this),
    # otherwise return it.
    result = closure[0]
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

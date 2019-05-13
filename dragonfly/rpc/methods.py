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

For RPC methods to work they must be added to the server with
:meth:`add_method`. For example::

    from dragonfly.engines import get_engine
    from dragonfly.rpc import RPCServer

    def get_engine_language():
        return get_engine().language

    server = RPCServer()
    server.add_method(get_engine_language)


Built-in RPC methods
============================================================================

"""

from six import string_types

from .. import get_engine, CompoundRule, MappingRule
from ..engines.base import MimicFailure


methods = []


def _add_method(m):
    methods.append(m)
    return m


@_add_method
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


@_add_method
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


@_add_method
def speak(text):
    """
    Speak the given *text* using text-to-speech using :meth:`engine.speak`.

    :param text: text to speak using text-to-speech
    :type text: str
    """
    if not isinstance(text, string_types):
        raise TypeError("text must be a string")

    return get_engine().speak(text)


@_add_method
def get_engine_language():
    """
    Get the current engine's language.

    :returns: language code
    :rtype: str
    """
    return get_engine().language

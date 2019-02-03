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
Available RPC methods
----------------------------------------------------------------------------


"""

from six import string_types

from jsonrpc.dispatcher import Dispatcher

from .. import get_engine, CompoundRule, MappingRule
from ..engines.base import MimicFailure

# Initialise a method dispatcher.
dispatcher = Dispatcher()


@dispatcher.add_method
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

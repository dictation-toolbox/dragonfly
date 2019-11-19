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
    This example command module demonstrates how to control the engine from
    grammars.

    This module can be activated in the same way as other
    Natlink macros by placing it in the "NatLink/MacroSystem" folder.

"""

import sys

from dragonfly import Grammar, MappingRule, get_engine, Function


#---------------------------------------------------------------------------
# Create this module's grammar.

grammar = Grammar("Engine control")


#---------------------------------------------------------------------------
# Create a mapping rule which maps things you can say to actions.

def disconnect():
    print("Disconnecting engine.")
    engine = get_engine()
    if engine.name == 'natlink' and 'natspeak' in sys.executable:
        print("Not calling disconnect() for embedded natlink.")
    else:
        engine.disconnect()


control_rule = MappingRule(
    name="control",
    mapping={
        # Stop recognising from the microphone and exit.
        "disconnect engine|stop recognizing": Function(disconnect),
    }
)

# Add the action rule to the grammar instance.
grammar.add_rule(control_rule)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None

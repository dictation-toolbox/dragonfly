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
    This module is a simple example of Dragonfly use.

    It shows how to use Dragonfly's Grammar, AppContext, and ActionRule
    classes.  This module can be activated in the same way as other
    Natlink macros by placing it in the My Documents\Natlink folder.
"""


from dragonfly.grammar.grammar     import Grammar
from dragonfly.grammar.context     import AppContext
from dragonfly.grammar.actionrule  import ActionRule
from dragonfly.grammar.elements    import Dictation
from dragonfly.actions.actions     import Key, Text


#---------------------------------------------------------------------------
# Create this module's grammar and the context under which it'll be active.

grammar_context = AppContext(executable="notepad")
grammar = Grammar("notepad_example", context=grammar_context)


#---------------------------------------------------------------------------
# Create an action rule which maps things you can say to actions.

command_rule = ActionRule(
        name="commands",    # Name of this rule.
        action_map={        # Dict of things to say -> actions.
                "save [file]":            Key("c-s"),
                "save [file] as":         Key("a-f, a"),
                "save [file] as <dict>":  Key("a-f, a/20") + Text("%(text)s"),
                "find <dict>":            Key("c-f/20") + Text("%(text)s\n"),
                },
        elements={          # Special elements in the keys of action_map.
                "dict": Dictation("text"),
                },
        exported=True       # Export this rule.
        )

# Add the action rule to the grammar instance.
grammar.add_rule(command_rule)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None

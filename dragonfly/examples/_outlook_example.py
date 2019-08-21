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

    It shows how to use Dragonfly's Grammar, AppContext, and MappingRule
    classes.  This module can be activated in the same way as other
    Natlink macros by placing it in the "NatLink/MacroSystem" folder.
"""

from dragonfly import (Grammar, AppContext, MappingRule, Choice,
                       Key, Text, Pause)


#---------------------------------------------------------------------------
# Create this module's grammar and the context under which it'll be active.

grammar_context = AppContext(executable="outlook")
grammar = Grammar("outlook_example", context=grammar_context)


#---------------------------------------------------------------------------
# Create a rule for static keyboard shortcuts.

static_rule = MappingRule(
    name="static",
    mapping={
             "new folder":                   Key("cs-e"),
             "new email":                    Key("cs-m"),
             "new appointment":              Key("cs-a"),
             "new meeting request":          Key("cs-q"),
             "new contact":                  Key("cs-c"),
             "new distribution list":        Key("cs-l"),
             "new note":                     Key("cs-n"),
             "new task":                     Key("cs-k"),

             "accept and edit":              Key("a-a, c, e, enter"),
             "accept and send":              Key("a-a, c, s, enter"),
             "accept without response":      Key("a-a, c, d, enter"),
             "tentative and edit":           Key("a-a, a, e, enter"),
             "tentative and send":           Key("a-a, a, s, enter"),
             "tentative without response":   Key("a-a, a, d, enter"),

             "folder":                       Key("c-y"),
            },
    )

# Add the action rule to the grammar instance.
grammar.add_rule(static_rule)


#---------------------------------------------------------------------------
# Create a rule for our list of folders.

folder_map = {
              "inbox":         "inbox",
              "sent":          "sent items",
              "deleted":       "deleted",
              "outbox":        "outbox",
             }

folder_rule = MappingRule(
    name="folder",
    mapping={
             "folder <folder>":   Key("c-1, home")
                                   + Text("%(folder)s\n")
                                   + Key("space, tab"),
             "move to <folder>":  Key("cs-v, home/10")
                                   + Text("%(folder)s")
                                   + Pause("75")
                                   + Key("enter"),
            },
    extras=[
            Choice("folder", folder_map),
           ],
    )

# Add the action rule to the grammar instance.
grammar.add_rule(folder_rule)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None

#
# This file is part of Dragonfly.
# (c) Copyright 2023 by Dane Finlay
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
    This module demonstrates how to use one of Dragonfly's dynamic language
    elements, DictLists, to create voice commands for setting, unsetting
    and printing variables in a dictionary.

    Dragonfly DictLists may be updated and modified without reloading a
    grammar.  DictLists are used in the same way as ordinary Python
    dictionaries.  Dragonfly also has a dynamic List class which works in
    the same way, but is used like a Python list instead of a dictionary.

    This module can be activated in the same way as other Natlink macros by
    placing it in the "NatLink/MacroSystem" folder.

"""

from dragonfly import (Grammar, MappingRule, Dictation, ListRef,
                       DictList, Text, Clipboard, Function)


#---------------------------------------------------------------------------
# Create this module's grammar.

grammar = Grammar("Variable List Example")


#---------------------------------------------------------------------------
# Create the DictList we will use in this module's grammar.
# DictLists, like rules, are components of grammars that are spoken via
#  special reference elements.

variable_list = DictList("variables")

# Add the list to the grammar instance.
# Note that this is not necessary in practice; Lists used by grammar rules
#  will be automatically added.
grammar.add_list(variable_list)


#---------------------------------------------------------------------------
# Define variable list functions to be used by voice commands below.

def add_var(new_var, text):
    # Set the value of variable *new_var* to *text*.
    set_var(new_var.format(), text)


def set_var(var, text):
    # Format *text*.
    text = text.format()

    # Set the value of variable *var* to *text*.
    variable_list[var] = text


def remove_var(var):
    # Remove variable *var* from the dictionary.
    del variable_list[var]


def add_var_clipboard(new_var):
    # Set the value of variable *new_var* to the current clipboard text.
    set_var_clipboard(new_var.format())


def set_var_clipboard(var):
    # Set the value of variable *var* to the current clipboard text, if any.
    # Get the current clipboard text.
    clipboard_text = Clipboard(from_system=True).text
    if not clipboard_text:
        clipboard_text = ""
    variable_list[var] = clipboard_text


def print_var(var):
    # Type the value of the variable *var*.
    Text(variable_list[var]).execute()


#---------------------------------------------------------------------------
# Create a mapping rule which maps things you can say to actions.
#
# Note the relationship between the *mapping* and *extras* keyword
#  arguments.  The extras is a list of Dragonfly elements which are
#  available to be used in the specs of the mapping.  In this example
#  the ListRef("var") extra makes it possible to use "<var>" within a
#  mapping spec and "%(var)s" within the associated action.

example_rule = MappingRule(
    name="example",    # The name of the rule.
    mapping={          # The mapping dict: spec -> action.
             "set <new_var> to <text>": Function(add_var),
             "set <var> to <text>": Function(set_var),
             "set <new_var> from clipboard": Function(add_var_clipboard),
             "set <var> from clipboard": Function(set_var_clipboard),
             "(remove | unset) variable <var>": Function(remove_var),
             "(type | print) <var>": Function(print_var),
            },
    extras=[           # Special elements in the specs of the mapping.
            # We use *ListRef* because we want the variable functions to get
            #  dictionary keys, not values.
            ListRef("var", variable_list),

            # Dictation elements are used to recognize new variable names
            #  and values.
            Dictation("new_var"),
            Dictation("text"),
           ],
)

# Add the rule to the grammar instance.
grammar.add_rule(example_rule)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None

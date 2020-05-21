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
    This module demonstrates the use of Dragonfly's CompoundRule class.

    It shows how to use Dragonfly's Grammar, AppContext, and CompoundRule
    classes.  This module can be activated in the same way as other
    Natlink macros by placing it in the "NatLink/MacroSystem" folder.

"""

from dragonfly import (Grammar, AppContext, CompoundRule, Choice, Dictation)


#---------------------------------------------------------------------------
# Create this module's grammar and the context under which it'll be active.

grammar_context = AppContext(executable="notepad")
grammar = Grammar("notepad_example_2", context=grammar_context)


#---------------------------------------------------------------------------
# Create a compound rule which demonstrates CompoundRule and Choice types.

class FoodGroupRule(CompoundRule):

    spec   = "(I ate <food> <time> | <time> I ate <food>) [and thought it was <opinion>]"
    time   = {
              "(two days ago | day before yesterday)":  2,
              "yesterday":                              1,
              "today":                                  0,
             }
    food   = {
              # Note: quoted words are sometimes required for Dragon to
              # recognize commands.

              # Quoted food words.
              # Uncomment these mappings if Dragon isn't recognizing the
              # 'food' extra.
              # "an orange":                      "fruit",
              # '("a Granny Smith" | an) apple':  "fruit",
              # '"a hamburger"':                  "meat",
              # '"a steak"':                      "meat",
              # '"a juicy steak"':                "meat",

              # Unquoted food words.
              # Comment these mappings if using the quoted words.
              "an orange":                      "fruit",
              "(a Granny Smith | an) apple":    "fruit",
              "an orange":                      "fruit",
              "a hamburger":                    "meat",
              "a [juicy] steak":                "meat",
             }
    extras = [
              Choice("time", time),
              Choice("food", food),
              Dictation("opinion"),
             ]

    def _process_recognition(self, node, extras):
        days_ago  = extras["time"]
        foodgroup = extras["food"]
        print("You ate %s %d days ago." % (foodgroup, days_ago))
        if "opinion" in extras:
            print("You thought it was %s." % (extras["opinion"]))

grammar.add_rule(FoodGroupRule())


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None

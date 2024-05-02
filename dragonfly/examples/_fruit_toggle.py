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
    This module demonstrates the use of the Dragonfly speech recognition
    library.

"""

from dragonfly import (Grammar, CompoundRule, Dictation)


#---------------------------------------------------------------------------
# Create a compound rule which demonstrates CompoundRule and Choice types.

class AppleRule(CompoundRule):
    spec = "I like apples [<text>]"
    extras = [Dictation("text")]
    def _process_recognition(self, node, extras):
        print("I like apples!  (%s)" % extras.get("text", ""))
        apple_rule.disable()
        banana_rule.enable()

class BananaRule(CompoundRule):
    spec = "I like bananas [<text>]"
    extras = [Dictation("text")]
    def _process_recognition(self, node, extras):
        print("I like bananas!  (%s)" % extras.get("text", ""))
        banana_rule.disable()
        apple_rule.enable()

apple_rule = AppleRule()
banana_rule = BananaRule()


#---------------------------------------------------------------------------
# Create this module's grammar.

grammar = Grammar("fruit toggle")
grammar.add_rule(apple_rule)
grammar.add_rule(banana_rule)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None

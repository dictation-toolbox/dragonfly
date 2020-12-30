#
# This file is part of Dragonfly.
# (c) Copyright 2020 by LexiconCode
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

    It shows how to use Dragonfly's Function action to call Python functions
    with the values associated with spoken Choice, Dictation and IntegerRef
    elements. This module can be activated in the same way as other
    Natlink macros by placing it in the "NatLink/MacroSystem" folder.

    This module requires the 'geocoder' Python package, which can be
    installed by running the following command:

      pip install geocoder

"""

import logging

import geocoder

from dragonfly import (Choice, Dictation, Function, Grammar, IntegerRef,
                       Key, MappingRule, Text, get_current_engine)


#---------------------------------------------------------------------------
# Define functions used by voice commands below.

def complete():
    print("Function is now complete.")


def cap_text(text):
    Text(text.upper()).execute()


def say_number(n):
    text = "I said number " + str(n)
    engine = get_current_engine()
    if engine:
        engine.speak(text)
    print(text)


def volume_control(n, volume_mode):
    for i in range(0, n):
        Key("volume" + volume_mode).execute()


data = {}
last_location = None
def get_location(location):
    global last_location
    last_location = location
    global data
    try:
        print(location)
        g = geocoder.osm(location.encode('utf-8'))
        data = g.json
    except (Exception) as e:
        log = logging.getLogger("location")
        log.exception("Error while getting data for location '%s': %s",
                      location, e)


def get_last_location_info(location_info):
    global last_location
    if not last_location:
        print('No location was specified. Say "get <location>" first.')
        return

    global data
    if not data:
        print("No data available for location '{0}'.".format(last_location))
    else:
        print(data.get(location_info))


def busy_func(fruit, animals, stuff, things):
    print(fruit)
    print(animals)
    print(stuff)
    print(things)


#---------------------------------------------------------------------------
# Create a mapping rule class which maps things you can say to actions.
#
# Note the relationship between the *mapping* and *extras* keyword
#  arguments.  The extras is a list of Dragonfly elements which are
#  available to be used in the specs of the mapping.  In this example
#  the IntegerRef("n") extra makes it possible to use "<n>" within a
#  mapping spec and pass an integer "n" to the associated action's
#  function.

class FunctionExamplesRule(MappingRule):
    mapping = {
        # Call the complete() function.
        "function complete": Function(complete),

        # Type capitalized text.
        "[dictation] capitalize <text>": Function(cap_text),

        # Say numbers.
        "say number <n>": Function(say_number),
        "say double number <n>": Function(lambda n: say_number(n * 2)),

        # Control the volume.
        "volume <volume_mode> [<n>]": Function(volume_control),

        # Retrieves address and country of <any location>.
        # 1. Say "get Yellowstone National Park".
        "get <location>":  Function(get_location),
        # The address and country of <any location> can be retrieved
        # afterwards.
        # 2. Say "what is the country".
        # 3. Say "what is the address".
        "what is [the] <location_info>": Function(get_last_location_info),

        # Print secret fruits and animals mapped to spelling words.
        # The values of 'stuff' and 'things' will also be printed.
        "secret <fruit> [<animals>]": Function(busy_func, stuff="shhhh...",
                                               things="more"),
    }

    extras = [
        IntegerRef("n", 1, 50),
        Dictation("text"),
        Dictation("location"),

        Choice("volume_mode", {
            "mute": "mute",
            "up": "up",
            "down": "down",
        }),

        Choice("fruit", {
            "alpha": "apple",
            "bravo": "blueberry",
            "charlie": "cherry",
        }),

        Choice("animals", {
            "delta": "dogs",
            "echo": "emus",
            "foxtrot": "foxes",
        }),

        Choice("location_info", {
            "address": "address",
            "country": "country",
        }),
    ]

    defaults = {
        "n": 1,
        "animals": "",
        "text": ""
    }


#---------------------------------------------------------------------------
# Create this module's grammar instance and add the rule to it.

grammar = Grammar("Function Examples")
grammar.add_rule(FunctionExamplesRule())


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None

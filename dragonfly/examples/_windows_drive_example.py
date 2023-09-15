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
    This module demonstrates how to use Dragonfly to create a voice command
    for opening any currently active Windows drive in a new explorer window.

    This module constrains the list of drive letters to active ones through
    use of Dragonfly's dynamic lists.  Dynamic lists allow the user to
    change parts of spoken commands without having to reload the grammar.

"""

import subprocess

import win32api

from dragonfly import (Grammar, CompoundRule, List, ListRef)


#---------------------------------------------------------------------------
# Create a compound rule for opening Windows drives in Windows explorer.

class OpenDriveRule(CompoundRule):
    # Define the command to be spoken.
    spec = "open <drive_letter> drive"

    # Define a dynamic list *drive_letters*, to be populated later.
    drive_letters_list = List("drive_letters")

    # Define extras that are part of the compound rule specification.
    #  These are the parts of *spec* in angled brackets.  In this case, the
    #  extra is a reference to the dynamic list defined above.
    extras = [
              ListRef("drive_letter", drive_letters_list)
             ]

    def _process_begin(self):
        # Retrieve a list of the system's current logical drives.
        system_drive_letters = win32api.GetLogicalDriveStrings()
        system_drive_letters = system_drive_letters.split(":\\\x00")[0:-1]

        # Do nothing further if the logical drive list has not changed.
        drive_letters_list = self.drive_letters_list
        if drive_letters_list == system_drive_letters: return

        # Update the dynamic *drive_letters* list to include only the
        #  currently active letters.  Use the context manager ('with') as
        #  an optimization; this ensures only one list update.
        with drive_letters_list:
            drive_letters_list.clear()
            drive_letters_list.extend(system_drive_letters)

    def _process_recognition(self, node, extras):
        # Retrieve the spoken drive letter.
        drive_letter = extras.get("drive_letter")

        # Open a Windows explorer window at the specified drive.
        subprocess.Popen(["explorer.exe", drive_letter + ":"])


open_drive_rule = OpenDriveRule()


#---------------------------------------------------------------------------
# Create this module's grammar.

grammar = Grammar("Windows drive example")
grammar.add_rule(open_drive_rule)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None

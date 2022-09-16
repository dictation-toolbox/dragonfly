#
# This file is part of Dragonfly.
# (c) Copyright 2022 by Dane Finlay
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

""" This module handles complex platform checks. """

import os


def is_x11():
    """
    Check for X11 by looking at the value of the *DISPLAY* environment
    variable.

    If the *DISPLAY* environment variable is present, and is in one of the
    two forms below, this function returns true.  Otherwise, it returns
    false.

    Acceptable forms of the *DISPLAY* variable:

        * [hostname]:displaynumber[.screennumber]

        * [protocol/hostname]:displaynumber[.screennumber]

    Note: Although this function parses *hostname* and *protocol/hostname*
    segments, no attempt is made to validate them.  The *displaynumber* and
    segments, however, must be a digit string, as does the *screennumber*,
    if it is present.
    """

    # Parse segments and delimiters from the env. variable.
    display = os.environ.get("DISPLAY", "")
    segments = ["", "", ""]
    delimiters = ["", ""]
    index = 0; current = "";
    for char in display:
        if index == 0 and char == ":" or index == 1 and char == ".":
            delimiters[index] = char
            segments[index] = current
            index += 1; current = "";
        else:
            current += char
    segments[index] += current

    # Validate each segment as necessary.
    hostname, display_number, screen_number = segments
    if not display_number.isdigit(): return False
    if len(delimiters[1]) > 0 and len(screen_number) == 0: return False
    if len(screen_number) > 0 and not screen_number.isdigit(): return False
    return True


#: Whether the value of the DISPLAY env. variable indicates an X11 session.
IS_X11 = is_x11()


if __name__ == '__main__':
    # Test the _is_x11() function.
    for string in ["unix/localhost:0", "localhost:0", "localhost:0.0",
                   ":0.0", ":0"]:
        #print(string)
        os.environ["DISPLAY"] = string
        assert is_x11()
    for string in ["", "localhost", "localhost:", "localhost:0.", ":",
                   "0.0", ":0:", ":0.", ":a", ":0.a", ":a.0", ":a.a"]:
        #print(string)
        os.environ["DISPLAY"] = string
        assert not is_x11()

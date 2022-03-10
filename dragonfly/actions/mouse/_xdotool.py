#
# This file is part of Dragonfly.
# (c) Copyright 2021 by Dane Finlay
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

from __future__                    import print_function

import locale
from subprocess                    import Popen, PIPE
import os
import sys

from six                           import binary_type

from dragonfly.actions.mouse._base import BaseButtonEvent, MoveEvent

#---------------------------------------------------------------------------
# Helper function for running xdotool commands.

def _run_xdotool_command(arguments):
    arguments = [str(arg) for arg in arguments]
    full_command = ["xdotool"] + arguments
    kwargs = dict(stdout=PIPE, stderr=PIPE)

    # Fork the process with setsid() if on a POSIX system.
    if os.name == 'posix':
        kwargs.update(dict(preexec_fn=os.setsid))

    # Execute the command with Popen, logging an error and re-raising
    # the exception on failure.
    try:
        p = Popen(full_command, **kwargs)
        stdout, stderr = p.communicate()
    except OSError as exception:
        raise exception

    # Decode output if it is binary.
    encoding = locale.getpreferredencoding()
    if isinstance(stdout, binary_type):
        stdout = stdout.decode(encoding)
    if isinstance(stderr, binary_type):
        stderr = stderr.decode(encoding)

    # Print error messages to stderr. Filter BadWindow messages.
    stderr = stderr.rstrip()
    if stderr:
        print(stderr, file=sys.stderr)

    # Return the process output and return code.
    return stdout.rstrip(), p.returncode


#---------------------------------------------------------------------------
# Functions and event delegate for getting and setting the cursor position.

def get_cursor_position():
    # Get the position of the cursor on the screen using xdotool.
    arguments = ["getmouselocation", "--shell"]
    stdout, returncode = _run_xdotool_command(arguments)
    result = None
    if returncode == 0:
        lines = stdout.split("\n")
        assert lines[0].startswith("X=")
        assert lines[1].startswith("Y=")
        x = int(lines[0][2:])
        y = int(lines[1][2:])
        result = (x, y)
    return result


def set_cursor_position(x, y):
    # Set the position of the cursor on the screen using xdotool.
    arguments = ["mousemove", str(x), str(y)]
    _, returncode = _run_xdotool_command(arguments)
    return returncode == 0


class MoveEventDelegate(object):

    @classmethod
    def get_position(cls):
        return get_cursor_position()

    @classmethod
    def set_position(cls, x, y):
        return set_cursor_position(x, y)


# Provide MoveEvent classes access to the cursor functions via a delegate.
MoveEvent.delegate = MoveEventDelegate

#---------------------------------------------------------------------------
# xdotool mouse button and wheel up/down flags.

# Note: The "four" and "five" buttons and the left/right scroll events are
# not supported by xdotool.


PLATFORM_BUTTON_FLAGS = {
    # ((button, event_type), down)
    # The inner pair is used here and below to be compatible with the
    # original Windows flags.
    "left":   (((1, 0), 1),  # down
               ((1, 0), 0)),  # up
    "right":  (((3, 0), 1),
               ((3, 0), 0)),
    "middle": (((2, 0), 1),
               ((2, 0), 0)),

    # We call these "four" and "five" because Windows calls them that.
    "four": ((("four", 0), 1),
             (("four", 0), 0)),
    "five": ((("five", 0), 1),
             (("five", 0), 0)),
}

PLATFORM_WHEEL_FLAGS = {
    # ((button, event_type), scroll_count)
    "wheelup": ((4, 1), 3),
    "stepup": ((4, 1), 1),
    "wheeldown": ((5, 1), 3),
    "stepdown": ((5, 1), 1),
    "wheelright": (("wheelright", 1), 3),
    "stepright": (("stepright", 1), 1),
    "wheelleft": (("wheelleft", 1), 3),
    "stepleft": (("stepleft", 1), 1),
}


#---------------------------------------------------------------------------
# xdotool event classes.


class ButtonEvent(BaseButtonEvent):

    def execute(self, window):
        # Construct xdotool arguments.
        arguments = []
        for ((button, event_type), flag) in self._flags:
            # Raise an error for unsupported buttons.
            if isinstance(button, str):
                event_type_s = "button" if event_type == 0 else "scroll"
                raise ValueError("Unsupported %s event: %s"
                                 % (event_type_s, button))

            # Handle click events.
            if event_type == 0:
                command = "mousedown" if flag else "mouseup"
                arguments.extend([command, str(button)])

            # Handle scroll events.
            else:
                arguments.extend([
                    "click", "--repeat", str(flag), "--delay", "0",
                    str(button)
                ])

        # Return early if *arguments* is empty.
        if len(arguments) == 0:
            return

        # Send events with xdotool.
        _run_xdotool_command(arguments)

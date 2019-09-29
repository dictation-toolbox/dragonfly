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

from pynput.mouse import Controller, Button

from ._base import BaseButtonEvent, MoveEvent


# Initialise a pynput mouse controller.
_controller = Controller()


#---------------------------------------------------------------------------
# Functions and event delegate for getting and setting the cursor position.

def get_cursor_position():
    return _controller.position


def set_cursor_position(x, y):
    _controller.position = (x, y)
    return True


class MoveEventDelegate(object):

    @classmethod
    def get_position(cls):
        return get_cursor_position()

    @classmethod
    def set_position(cls, x, y):
        return set_cursor_position(x, y)


# Set MoveEvent's delegate. This allows us to set platform-specific
# functions for getting and setting the cursor position without having
# to do a lot of sub-classing for no good reason.
MoveEvent.delegate = MoveEventDelegate()

#---------------------------------------------------------------------------
# Pynput mouse button and wheel up/down flags.


def get_button(name):
    # If possible, get a Button from the name.
    # This allows button and wheel flags to work, at least partially, on
    # multiple platforms.
    return getattr(Button, name, None)


PLATFORM_BUTTON_FLAGS = {
    # ((button, event_type), down)
    # The inner pair is used here and below to be compatible with the
    # original Windows flags.
    "left":   (((get_button("left"), 0), 1),  # down
               ((get_button("left"), 0), 0)),  # up
    "right":  (((get_button("right"), 0), 1),
               ((get_button("right"), 0), 0)),
    "middle": (((get_button("middle"), 0), 1),
               ((get_button("middle"), 0), 0)),

    # We call these "four" and "five" because Windows calls them that.
    # These buttons typically behave as browser back and forward media keys.
    "four": (((get_button("button8"), 0), 1),
             ((get_button("button8"), 0), 0)),
    "five": (((get_button("button9"), 0), 1),
             ((get_button("button9"), 0), 0)),
}

PLATFORM_WHEEL_FLAGS = {
    # ((button, event_type), scroll_count)
    "wheelup": ((get_button("scroll_up"), 1), 3),
    "stepup": ((get_button("scroll_up"), 1), 1),
    "wheeldown": ((get_button("scroll_down"), 1), 3),
    "stepdown": ((get_button("scroll_down"), 1), 1),
    "wheelright": ((get_button("scroll_right"), 1), 3),
    "stepright": ((get_button("scroll_right"), 1), 1),
    "wheelleft": ((get_button("scroll_left"), 1), 3),
    "stepleft": ((get_button("scroll_left"), 1), 1),
}


#---------------------------------------------------------------------------
# pynput event classes.


class ButtonEvent(BaseButtonEvent):

    def execute(self, window):
        for ((button, event_type), flag) in self._flags:
            # Check if the button is unknown.
            if button is None:
                event_type_s = "button" if event_type == 0 else "scroll"
                raise ValueError("Unsupported %s event" % event_type_s)

            if event_type == 0:  # Button press event
                if flag:
                    _controller.press(button)
                else:
                    _controller.release(button)
            elif event_type == 1:  # Scroll event
                _controller.click(button, flag)

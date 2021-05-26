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

from talon import ctrl

from ._base import BaseButtonEvent, MoveEvent


#---------------------------------------------------------------------------
# Functions and event delegate for getting and setting the cursor position.

def get_cursor_position():
    ctrl.mouse_pos()


def set_cursor_position(x, y):
    ctrl.mouse_move(x, y)
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


_buttons = {
    'left': 0,
    'right': 1,
    'middle': 2,
    'four': 3,
    'five': 4,
}
def get_button(name):
    return buttons.get(name, None)


PLATFORM_BUTTON_FLAGS = {
    # ((button, event_type), down)
    # The inner pair is used here and below to be compatible with the
    # original Windows flags.
    "left":   (((0, 0), 1),  # down
               ((0, 0), 0)),  # up
    "right":  (((1, 0), 1),
               ((2, 0), 0)),
    "middle": (((2, 0), 1),
               ((2, 0), 0)),

    # We call these "four" and "five" because Windows calls them that.
    # These buttons typically behave as browser back and forward media keys.
    "four": (((3, 0), 1),
             ((3, 0), 0)),
    "five": (((4, 0), 1),
             ((4, 0), 0)),
}

PLATFORM_WHEEL_FLAGS = {
    # ((button, event_type), scroll_count)
    "wheelup": (('up', 1), 3),
    "stepup": (('up', 1), 1),
    "wheeldown": (('down', 1), 3),
    "stepdown": (('down', 1), 1),
    "wheelright": (('right', 1), 3),
    "stepright": (('right', 1), 1),
    "wheelleft": (('left', 1), 3),
    "stepleft": (('left', 1), 1),
}


#---------------------------------------------------------------------------
# event classes.


class ButtonEvent(BaseButtonEvent):

    def execute(self, window):
        for ((button, event_type), flag) in self._flags:
            # Check if the button is unknown.
            if button is None:
                event_type_s = "button" if event_type == 0 else "scroll"
                raise ValueError("Unsupported %s event" % event_type_s)

            if event_type == 0:  # Button press event
                ctrl.mouse_click(button, down=bool(flag))
            elif event_type == 1:  # Scroll event
                if button == 'up':
                    ctrl.mouse_scroll(y=-flag)
                elif button == 'down':
                    ctrl.mouse_scroll(y=flag)
                elif button == 'left':
                    ctrl.mouse_scroll(x=-flag)
                elif button == 'right':
                    ctrl.mouse_scroll(x=flag)

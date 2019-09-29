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

import time

from dragonfly.actions.action_base import ActionError
from dragonfly.windows import monitors


#---------------------------------------------------------------------------
# Functions and event delegate for getting and setting the cursor position.

def get_cursor_position():
    message = ("Getting the cursor position is not implemented on this "
               "platform!")
    raise NotImplementedError(message)


def set_cursor_position(x, y):
    message = ("Setting the cursor position is not implemented on this "
               "platform!")
    raise NotImplementedError(message)


class MoveEventDelegate(object):

    @classmethod
    def get_position(cls):
        return get_cursor_position()

    @classmethod
    def set_position(cls, x, y):
        return set_cursor_position(x, y)


#---------------------------------------------------------------------------
# Mouse button and wheel up/down flags.
# These flags should be overridden for each supported platform.

PLATFORM_BUTTON_FLAGS = {
    "left":   ((1, 1),   # down
               (1, 0)),  # up
    "right":  ((2, 1),
               (2, 0)),
    "middle": ((3, 1),
               (3, 0)),
    "four":   ((4, 1),
               (4, 0)),
    "five":   ((5, 1),
               (5, 0)),
}


PLATFORM_WHEEL_FLAGS = {
    "wheelup": (1, 120),
    "stepup": (1, 40),
    "wheeldown": (1, -120),
    "stepdown": (1, -40),
    "wheelright": (2, 120),
    "stepright": (2, 40),
    "wheelleft": (2, -120),
    "stepleft": (2, -40),
}


#---------------------------------------------------------------------------
# Event classes.


class EventBase(object):

    def execute(self, window):
        pass


class MoveEvent(EventBase):

    # Set the event delegate. This allows us to set platform-specific
    # functions for getting and setting the cursor position without having
    # to do a lot of sub-classing for no good reason.
    delegate = MoveEventDelegate()

    def __init__(self, from_left, horizontal, from_top, vertical):
        self.from_left = from_left
        self.horizontal = horizontal
        self.from_top = from_top
        self.vertical = vertical
        EventBase.__init__(self)

    def _move_relative(self, rectangle):
        if self.from_left:  horizontal = rectangle.x1
        else:               horizontal = rectangle.x2
        if isinstance(self.horizontal, float):
            distance = self.horizontal * rectangle.dx
        else:
            distance = self.horizontal
        horizontal += distance

        if self.from_top:   vertical = rectangle.y1
        else:               vertical = rectangle.y2
        if isinstance(self.vertical, float):
            distance = self.vertical * rectangle.dy
        else:
            distance = self.vertical
        vertical += distance

        self._move_mouse(horizontal, vertical)

    def _get_position(self):
        return self.delegate.get_position()

    def _move_mouse(self, horizontal, vertical):
        self.delegate.set_position(horizontal, vertical)


class MoveWindowEvent(MoveEvent):

    def execute(self, window):
        self._move_relative(window.get_position())


class MoveScreenEvent(MoveEvent):

    def execute(self, window):
        # Move the mouse relative to the first monitor's rectangle.
        # Do nothing if there are no monitors in the list.
        if monitors:
            self._move_relative(monitors[0].rectangle)


class BaseButtonEvent(EventBase):

    def __init__(self, *flags):
        EventBase.__init__(self)
        self._flags = flags

    def execute(self, window):
        message = ("Mouse button events are not implemented for this "
                   "platform!")
        raise NotImplementedError(message)


class MoveRelativeEvent(MoveEvent):

    def __init__(self, horizontal, vertical):
        MoveEvent.__init__(self, None, None, None, None)
        self.horizontal = horizontal
        self.vertical = vertical

    def execute(self, window):
        position = self._get_position()
        if not position:
            raise ActionError("Failed to retrieve cursor position.")
        horizontal = position[0] + self.horizontal
        vertical   = position[1] + self.vertical
        self._move_mouse(horizontal, vertical)


class PauseEvent(EventBase):

    def __init__(self, interval):
        EventBase.__init__(self)
        self._interval = interval

    def execute(self, window):
        time.sleep(self._interval)

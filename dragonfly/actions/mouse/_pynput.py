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

from pynput.mouse                   import Controller, Button

from dragonfly.actions.mouse._base  import BaseButtonEvent, MoveEvent


_controller = None

def _init_controller():
    global _controller
    if _controller is None:
        _controller = Controller()


#---------------------------------------------------------------------------
# Functions and event delegate for getting and setting the cursor position.

def get_cursor_position():
    # Initialize the pynput mouse controller, if necessary.
    _init_controller()

    # Return the cursor position.
    return _controller.position


def set_cursor_position(x, y):
    # Initialize the pynput mouse controller, if necessary.
    _init_controller()

    # Set the cursor position.
    _controller.position = (x, y)
    return True


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
    # button  ->  ((button, event_type), step_count)
    "wheelup":    (("stepup",    2),  3),
    "stepup":     (("stepup",    2),  1),
    "wheeldown":  (("stepdown",  2), -3),
    "stepdown":   (("stepdown",  2), -1),
    "wheelright": (("stepright", 2),  3),
    "stepright":  (("stepright", 2),  1),
    "wheelleft":  (("stepleft",  2), -3),
    "stepleft":   (("stepleft",  2), -1),
}


#---------------------------------------------------------------------------
# pynput event classes.


class ButtonEvent(BaseButtonEvent):

    def execute(self, window):
        # Initialize the pynput mouse controller, if necessary.
        _init_controller()

        # Pre-process event flags.
        # - Raise an error if an unsupported event is found.
        # - Combine down/up events so that the `click' function may be used
        #    where appropriate.
        events = []
        if len(self._flags) > 0: events.append(self._flags[0])
        for event in self._flags[1:]:
            ((button, event_type), flag) = event
            if button is None:
                message = "Unsupported mouse %s event"
                if event_type == 0: message = message % "scroll"
                else:               message = message % "button"
                raise ValueError(message)

            # Is this event compatible with the last one-to-two events?
            # Note: Button events are joined like this because the *pynput*
            #  `click' controller method must be used for double/triple
            #  clicking on macOS.
            prev_event = events.pop()
            ((prev_button, prev_event_type), prev_flag) = prev_event
            if (prev_button == button and prev_flag and not flag and
                    prev_event_type == event_type == 0):
                event = ((button, 1), 1)
                if len(events) > 0:
                    # Join successive click events.
                    prev_event = events.pop()
                    ((prev_button, prev_event_type), prev_flag) = prev_event
                    if prev_button == button and prev_event_type == 1:
                        event = ((button, 1), prev_flag + 1)
                    else:
                        events.append(prev_event)
            else:
                events.append(prev_event)

            events.append(event)

        # Process mouse events.
        for event in events:
            ((button, event_type), flag) = event
            # Button press events.
            if event_type == 0:
                if flag == 1:
                    _controller.press(button)
                else:
                    _controller.release(button)
            elif event_type == 1:
                _controller.click(button, flag)

            # Scroll events.
            elif event_type == 2:
                if button == "stepup" or button == "stepdown":
                    _controller.scroll(0, flag)
                else:
                    _controller.scroll(flag, 0)

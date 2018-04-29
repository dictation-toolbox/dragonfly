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
Mouse action
============================================================================

This section describes the :class:`Mouse` action object.  This type of 
action is used for controlling the mouse cursor and clicking mouse
button.

Below you'll find some simple examples of :class:`Mouse` usage, followed 
by a detailed description of the available mouse events.


Example mouse actions
............................................................................

The following code moves the mouse cursor to the center of the foreground 
window (``(0.5, 0.5)``) and then clicks the left mouse button once 
(``left``)::

    # Parentheses ("(...)") give foreground-window-relative locations.
    # Fractional locations ("0.5", "0.9") denote a location relative to
    #  the window or desktop, where "0.0, 0.0" is the top-left corner
    #  and "1.0, 1.0" is the bottom-right corner.
    action = Mouse("(0.5, 0.5), left")
    action.execute()

The line below moves the mouse cursor to 100 pixels left of the desktop's 
right edge and 250 pixels down from its top edge (``[-100, 250]``), and 
then double clicks the right mouse button (``right:2``)::

    # Square brackets ("[...]") give desktop-relative locations.
    # Integer locations ("1", "100", etc.) denote numbers of pixels.
    # Negative numbers ("-100") are counted from the right-edge or the
    #  bottom-edge of the desktop or window.
    Mouse("[-100, 250], right:2").execute()

The following command drags the mouse from the top right corner of the 
foreground window (``(0.9, 10), left:down``) to the bottom left corner 
(``(25, -0.1), left:up``)::

    Mouse("(0.9, 10), left:down, (25, -0.1), left:up").execute()

The code below moves the mouse cursor 25 pixels right and 25 pixels up
(``<25, -25>``)::

    # Angle brackets ("<...>") move the cursor from its current position
    #  by the given number of pixels.
    Mouse("<25, -25>").execute()


Mouse specification format
............................................................................

The *spec* argument passed to the :class:`Mouse` constructor specifies 
which mouse events will be emulated.  It is a string consisting of one or 
more comma-separated elements.  Each of these elements has one of the 
following possible formats:

Mouse movement actions:

 - location is absolute on the entire desktop:
   ``[`` *number* ``,`` *number* ``]``
 - location is relative to the foreground window:
   ``(`` *number* ``,`` *number* ``)``
 - move the cursor relative to its current position:
   ``<`` *pixels* ``,`` *pixels* ``>``

In the above specifications, the *number* and *pixels* have the 
following meanings:

 - *number* -- can specify a number of pixels or a fraction of
   the reference window or desktop.  For example:

    - ``(10, 10)`` -- 10 pixels to the right and down from the
      foreground window's left-top corner
    - ``(0.5, 0.5)`` -- center of the foreground window

 - *pixels* -- specifies the number of pixels

Mouse button-press action:
   *keyname* [``:`` *repeat*] [``/`` *pause*]

 - *keyname* -- Specifies which mouse button to click:

    - ``left`` -- left mouse button key
    - ``middle`` -- middle mouse button key
    - ``right`` -- right mouse button key

 - *repeat* -- Specifies how many times the button should be clicked:

    - ``0`` -- don't click the button, this is a no-op
    - ``1`` -- normal button click
    - ``2`` -- double-click
    - ``3`` -- triple-click

 - *pause* --
   Specifies how long to pause *after* clicking the button.  The value
   should be an integer giving in hundredths of a second.  For example,
   ``/100`` would mean one second, and ``/50`` half a second.

Mouse button-hold or button-release action:
   *keyname* ``:`` *hold-or-release* [``/`` *pause*]

 - *keyname* -- Specifies which mouse button to click; same as above.

 - *hold-or-release* --
   Specified whether the button will be held down or released:

    - ``down`` -- hold the button down
    - ``up`` -- release the button

 - *pause* --
   Specifies how long to pause *after* clicking the button; same as above.


Mouse class reference
............................................................................

"""

import time
import win32con
import win32gui
from ctypes             import windll, pointer, c_long, c_ulong, Structure
from .sendinput         import MouseInput, make_input_array, send_input_array
from .action_base       import DynStrActionBase, ActionError
from ..windows.window   import Window
from ..windows.monitor  import monitors


#---------------------------------------------------------------------------

class _point_t(Structure):
    _fields_ = [
                ('x',  c_long),
                ('y',  c_long),
               ]

def get_cursor_position():
    point = _point_t()
    result = windll.user32.GetCursorPos(pointer(point))
    if result:  return (point.x, point.y)
    else:       return None

def set_cursor_position(x, y):
    result = windll.user32.SetCursorPos(c_long(int(x)), c_long(int(y)))
    if result:  return False
    else:       return True


#---------------------------------------------------------------------------

class _EventBase(object):

    def execute():
        pass


class _Move(_EventBase):

    def __init__(self, from_left, horizontal, from_top, vertical):
        self.from_left = from_left
        self.horizontal = horizontal
        self.from_top = from_top
        self.vertical = vertical
        _EventBase.__init__(self)

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

    def _move_mouse(self, horizontal, vertical):
        set_cursor_position(horizontal, vertical)


class _MoveWindow(_Move):

    def execute(self, window):
        self._move_relative(window.get_position())


class _MoveScreen(_Move):

    def execute(self, window):
        self._move_relative(monitors[0].rectangle)


class _MoveRelative(_Move):

    def __init__(self, horizontal, vertical):
        _Move.__init__(self, None, None, None, None)
        self.horizontal = horizontal
        self.vertical = vertical

    def execute(self, window):
        position = get_cursor_position()
        if not position:
            raise ActionError("Failed to retrieve cursor position.")
        horizontal = position[0] + self.horizontal
        vertical   = position[1] + self.vertical
        self._move_mouse(horizontal, vertical)


class _Button(_EventBase):

    def __init__(self, *flags):
        _EventBase.__init__(self)
        self._flags = flags

    def execute(self, window):
        zero = pointer(c_ulong(0))
        inputs = [MouseInput(0, 0, 0, flag, 0, zero)
                  for flag in self._flags]
        array = make_input_array(inputs)
        send_input_array(array)


class _Pause(_EventBase):

    def __init__(self, interval):
        _EventBase.__init__(self)
        self._interval = interval

    def execute(self, window):
        time.sleep(self._interval)


#---------------------------------------------------------------------------

class Mouse(DynStrActionBase):
    """ Action that sends mouse events. """

    def __init__(self, spec=None, static=False):
        """
            Arguments:
             - *spec* (*str*) -- the mouse actions to execute
             - *static* (boolean) --
               if *True*, do not dynamically interpret *spec*
               when executing this action

        """
        DynStrActionBase.__init__(self, spec=spec, static=static)

    def _parse_spec(self, spec):
        """ Convert the given *spec* to keyboard events. """
        events = []
        parts = self._split_parts(spec)
        for part in parts:
            handled = False
            for handler in self._handlers:
                try:
                    if handler(self, part, events):
                        handled = True
                        break
                except Exception as e:
                    continue
            if not handled:
                raise ActionError("Invalid mouse spec: %r (in %r)"
                                  % (part, spec))
        return events

    def _parse_position_pair(self, spec):
        parts = spec.split(",")
        if len(parts) != 2:
            raise ValueError("Invalid position pair spec: %r" % spec)

        h_origin, h_value = self._parse_position(parts[0])
        v_origin, v_value = self._parse_position(parts[1])

        return (h_origin, h_value, v_origin, v_value)

    def _process_window_position(self, spec, events):
        if not spec.startswith("(") or not spec.endswith(")"):
            return False
        h_origin, h_value, v_origin, v_value = self._parse_position_pair(spec[1:-1])
        event = _MoveWindow(h_origin, h_value, v_origin, v_value)
        events.append(event)
        return True

    def _process_screen_position(self, spec, events):
        if not spec.startswith("[") or not spec.endswith("]"):
            return False
        h_origin, h_value, v_origin, v_value = self._parse_position_pair(spec[1:-1])
        event = _MoveScreen(h_origin, h_value, v_origin, v_value)
        events.append(event)
        return True

    def _process_relative_position(self, spec, events):
        if not spec.startswith("<") or not spec.endswith(">"):
            return False
        parts = spec[1:-1].split(",")
        if len(parts) != 2:
            return False
        horizontal = int(parts[0])
        vertical   = int(parts[1])
        event = _MoveRelative(horizontal, vertical)
        events.append(event)
        return True

    _button_flags = {
                     "left":   (win32con.MOUSEEVENTF_LEFTDOWN,
                                win32con.MOUSEEVENTF_LEFTUP),
                     "right":  (win32con.MOUSEEVENTF_RIGHTDOWN,
                                win32con.MOUSEEVENTF_RIGHTUP),
                     "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN,
                                win32con.MOUSEEVENTF_MIDDLEUP),
                    }

    def _process_button(self, spec, events):
        parts = spec.split(":", 1)
        button = parts[0].strip()
        if len(parts) == 1:  special = 1
        else:                special = parts[1].strip()

        if button not in self._button_flags:
            return False
        flag_down, flag_up = self._button_flags[button]

        if special == "down":
            event = _Button(flag_down)
        elif special == "up":
            event = _Button(flag_up)
        else:
            try:
                repeat = int(special)
            except ValueError:
                return False
            flag_series = (flag_down, flag_up) * repeat
            event = _Button(*flag_series)

        events.append(event)
        return True

    def _process_pause(self, spec, events):
        if not spec.startswith("/"):
            return False
        interval = float(spec[1:]) / 100
        event = _Pause(interval)
        events.append(event)
        return True

    _handlers = [
                 _process_window_position,
                 _process_screen_position,
                 _process_relative_position,
                 _process_button,
                 _process_pause,
                ]

    def _parse_position(self, spec):
        spec = spec.strip()

        if spec.startswith("-"):  origin = False
        else:                     origin = True

        if spec.find(".") != -1:  value = float(spec)
        else:                     value = int(spec)

        return (origin, value)

    def _split_parts(self, spec):

        delimiters = ["()", "[]", "<>"]

        parts = spec.split(",")
        items = []
        while parts:
            part = parts.pop(0).strip()

            found_delimiter = False
            for begin, end in delimiters:
                if begin not in part:
                    continue

                item = [part]
                while parts:
                    part = parts.pop(0)
                    item.append(part)
                    if end in part:
                        break
                if end not in part:
                    raise Exception("No closing delimiter found for %r" % item[0])

                new_item = ",".join(item)
                found_delimiter = True
                break

            if not found_delimiter:
                new_item = part

            if "/" in new_item:
                before, after = new_item.split("/", 1)
                items.append(before.strip())
                items.append("/" + after.strip())
            else:
                items.append(new_item)

        return items


    #-----------------------------------------------------------------------

    def _execute_events(self, events):
        """ Send events. """
        window = Window.get_foreground()
        for event in events:
            event.execute(window)

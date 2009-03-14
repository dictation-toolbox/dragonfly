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


#m("<0,3>").execute()
#from time import sleep; from dragonfly import Mouse as m
#sleep(2);m("(-5,0.5), middle:down, <0,3>").execute()




"""
Mouse action
============================================================================

This section describes the :class:`Text` action object. This type of 
action is used for typing text into the foreground application.

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
    result = windll.user32.SetCursorPos(x, y)
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
        print 'h',horizontal, distance
        horizontal += distance

        if self.from_top:   vertical = rectangle.y1
        else:               vertical = rectangle.y2
        if isinstance(self.vertical, float):
            distance = self.vertical * rectangle.dy
        else:
            distance = self.vertical
        vertical += distance

        print "moving:", horizontal, vertical
        self._move_mouse(horizontal, vertical)

    def _move_mouse(self, horizontal, vertical):
        handle = windll.user32.GetDC(0)
        horzres = windll.gdi32.GetDeviceCaps(handle, win32con.HORZRES)
        vertres = windll.gdi32.GetDeviceCaps(handle, win32con.VERTRES)
        horizontal = int(float(horizontal) / horzres * 0x10000)
        vertical   = int(float(vertical)   / vertres * 0x10000)

        flags = win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE
        null = pointer(c_ulong(0))
        input = MouseInput(horizontal, vertical, 0, flags, 0, null)
        array = make_input_array([input])
        send_input_array(array)


class _MoveWindow(_Move):

    def execute(self, window):
        print self.__class__.__name__
        self._move_relative(window.get_position())


class _MoveScreen(_Move):

    def execute(self, window):
        print self.__class__.__name__
        self._move_relative(monitors[0].rectangle)


class _MoveRelative(_Move):

    def __init__(self, horizontal, vertical):
        _Move.__init__(self, None, None, None, None)
        self.horizontal = horizontal
        self.vertical = vertical

    def execute(self, window):
        position = get_cursor_position()
        print position
        if not position:
            raise ActionError("Failed to retrieve cursor position.")
        horizontal = position[0] + self.horizontal
        vertical   = position[1] + self.vertical
        print self.__class__.__name__, "move relative", position, "->", (horizontal, vertical)
        print 'pos', (horizontal, vertical)
        self._move_mouse(horizontal, vertical)
#        result = set_cursor_position(horizontal, vertical)
#        if not result:
#            raise ActionError("Failed to set cursor position.")


class _Button(_EventBase):

    def __init__(self, *flags):
        _EventBase.__init__(self)
        null = pointer(c_ulong(0))
        print "flags", flags
        flags = [win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP]
        inputs = [MouseInput(0, 0, 0, flag, 0, null) for flag in flags]
        self._array = make_input_array(inputs)

    def execute(self, window):
        print self.__class__.__name__, "buttons", self._array
        send_input_array(self._array)


class _Pause(_EventBase):

    def __init__(self, interval):
        _EventBase.__init__(self)
        self._interval = interval

    def execute(self, window):
        print self.__class__.__name__, "sleeping", self._interval
        time.sleep(self._interval)


#---------------------------------------------------------------------------

class Mouse(DynStrActionBase):
    """
        Action that sends mouse events.

        Arguments:
         - *spec* (*str*) -- the mouse actions to execute
         - *static* (boolean) --
           if *True*, do not dynamically interpret *spec*
           when executing this action

    """

    def __init__(self, spec=None, static=False):
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
                except Exception, e:
                    print 'argh', e
                    continue
            if not handled:
                raise ActionError("Invalid mouse spec: %r (in %r)"
                                  % (part, spec))
        print events
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
        if len(parts) == 1:  special = "1"
        else:                special = parts[1].strip()

        if button not in self._button_flags:
            return False
        flag_down, flag_up = self._button_flags[button]

        if special in ("0", "1", "2", "3"):
            repeat = int(special)
            flag_series = (flag_down, flag_up) * repeat
            event = _Button(*flag_series)
        elif special == "down":
            event = _Button(flag_down)
        elif special == "up":
            event = _Button(flag_up)
        else:
            return False

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

        print "%r -> %r" % (spec, items)
        return items


    #-----------------------------------------------------------------------

    def _execute_events(self, events):
        """ Send events. """
        window = Window.get_foreground()
        for event in events:
            print 'exec', event
            event.execute(window)

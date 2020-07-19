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
Base Window class
============================================================================

"""

# pylint: disable=W0622,R0904
# Suppress warnings about redefining the built-in 'id' function and too many
# public methods.

from locale import getpreferredencoding

from six import string_types, integer_types, binary_type

from .monitor import monitors
from .rectangle import unit
from .window_movers import window_movers

#===========================================================================


class BaseWindow(object):
    """
        The base Window class for controlling and placing windows.

    """

    #-----------------------------------------------------------------------
    # Class attributes to retrieve existing Window objects.

    _windows_by_name = {}
    _windows_by_id = {}

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_window(cls, id):
        """
        Get a :class:`Window` object given a window id.

        Given the same id, this method will return the same object.
        """
        if id in cls._windows_by_id:
            window = cls._windows_by_id[id]
        else:
            window = cls(id)
            cls._windows_by_id[id] = window
        return window

    @classmethod
    def get_foreground(cls):
        """ Get the foreground window. """
        raise NotImplementedError()

    @classmethod
    def get_matching_windows(cls, executable=None, title=None):
        """
        Find windows with a matching executable or title.

        Window searches are case-insensitive.

        If neither parameter is be specified, then it is effectively the
        same as calling :meth:`get_all_windows`.

        :param executable: -- part of the filename of the application's
           executable to which the target window belongs; not case
           sensitive.
        :param title: -- part of the title of the target window; not case
           sensitive.
        :type executable: str
        :type title: str
        :rtype: list
        """
        # Make window searches case-insensitive.
        if executable:
            executable = executable.lower()
        if title:
            title = title.lower()

        matching = []
        for window in cls.get_all_windows():
            if executable:
                if window.executable.lower().find(executable) == -1:
                    continue
            if title:
                if window.title.lower().find(title) == -1:
                    continue
            matching.append(window)
        return matching

    @classmethod
    def get_all_windows(cls):
        """ Get a list of all windows. """
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, id):
        self._id = None
        self.id = id
        self._names = set()

    def __repr__(self):
        args = list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    #-----------------------------------------------------------------------
    # Methods that control attribute access.

    @property
    def id(self):
        """ Protected access to id attribute. """
        return self._id

    @id.setter
    def id(self, value):
        self._set_id(value)

    def _set_id(self, id):
        if not isinstance(id, integer_types):
            raise TypeError("Window id/handle must be integer or long,"
                            " but received {0!r}".format(id))
        self._id = id
        self._windows_by_id[id] = self

    # The 'handle' and '_handle' attributes have been kept in for backwards-
    # compatibility. They just reference the BaseWindow 'id' property.

    handle = property(fget=lambda self: self._id,
                      fset=_set_id,
                      doc="Protected access to handle attribute.")
    _handle = property(fget=lambda self: self._id)

    def _get_name(self):
        if not self._names:
            return None
        for name in self._names:
            return name

    def _set_name(self, name):
        assert isinstance(name, string_types)
        self._names.add(name)
        self._windows_by_name[name] = self

    name = property(fget=_get_name,
                    fset=_set_name,
                    doc="Protected access to name attribute.")

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def _get_window_text(self):
        # Method to get the window title.
        raise NotImplementedError()

    def _get_class_name(self):
        # Method to get the window class name.
        raise NotImplementedError()

    def _get_window_module(self):
        # Method to get the window executable.
        raise NotImplementedError()

    def _get_window_pid(self):
        # Method to get the window process ID.
        raise NotImplementedError()

    @property
    def title(self):
        """ Read-only access to the window's title. """
        window_text = self._get_window_text()
        # PY2
        if isinstance(window_text, binary_type):
            return window_text.decode(getpreferredencoding())
        else:
            return window_text

    @property
    def classname(self):
        """ Read-only access to the window's class name. """
        return self._get_class_name()

    #: Alias of :attr:`classname`.
    cls_name = classname

    @property
    def executable(self):
        """ Read-only access to the window's executable. """
        return self._get_window_module()

    @property
    def pid(self):
        """
        Read-only access to the window's process ID.

        This will be the PID of the window's process, not any subprocess.

        If the window has no associated process id, this will return
        ``None``.

        :returns: pid
        :rtype: int | None
        """
        return self._get_window_pid()

    @property
    def is_minimized(self):
        """ Whether the window is currently minimized. """
        raise NotImplementedError()

    @property
    def is_maximized(self):
        """ Whether the window is currently maximized. """
        raise NotImplementedError()

    @property
    def is_visible(self):
        """
        Whether the window is currently visible.

        This may be indeterminable for some windows.
        """
        raise NotImplementedError()

    def matches(self, context):
        """ Whether the window matches the given context. """
        return context.matches(self.executable, self.title, self.handle)

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        """
        Method to get the window's position as a :class:`Rectangle` object.

        :returns: window position
        :rtype: Rectangle
        """
        raise NotImplementedError()

    def set_position(self, rectangle):
        """
        Method to set the window's position using a :class:`Rectangle`
        object.

        :param rectangle: window position
        :type rectangle: Rectangle
        """
        raise NotImplementedError()

    def get_containing_monitor(self):
        """
        Method to get the :class:`Monitor` containing the window.

        This checks which monitor contains the center of the window.

        :returns: containing monitor
        :rtype: Monitor
        """
        center = self.get_position().center
        for monitor in monitors:
            if monitor.rectangle.contains(center):
                return monitor
        # Fall through, return first monitor.
        return monitors[0]

    def get_normalized_position(self):
        """
        Method to get the window's normalized position.

        This is useful when working with multiple monitors.

        :returns: normalized position
        :rtype: Rectangle
        """
        monitor = self.get_containing_monitor()
        rectangle = self.get_position()
        rectangle.renormalize(monitor.rectangle, unit)
        return rectangle

    def set_normalized_position(self, rectangle, monitor=None):
        """
        Method to get the window's normalized position.

        This is useful when working with multiple monitors.

        :param rectangle: window position
        :type rectangle: Rectangle
        :param monitor: monitor to normalize to (default: the first one).
        :type monitor: Monitor
        """
        if not monitor:
            monitor = self.get_containing_monitor()

        rectangle.renormalize(unit, monitor.rectangle)
        self.set_position(rectangle)

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        """ Minimize the window (if possible). """
        raise NotImplementedError()

    def maximize(self):
        """ Maximize the window (if possible). """
        raise NotImplementedError()

    def close(self):
        """ Close the window (if possible). """
        raise NotImplementedError()

    def restore(self):
        """ Restore the window if it is minimized or maximized. """
        raise NotImplementedError()

    def set_foreground(self):
        """ Set the window as the foreground (active) window. """
        raise NotImplementedError()

    def set_focus(self):
        """
        Set the window as the active window without raising it.

        *Note*: this method will behave like :meth:`set_foreground()` in
        environments where this isn't possible.
        """
        raise NotImplementedError()

    def move(self, rectangle, animate=None):
        """
        Move the window, optionally animating its movement.

        :param rectangle: new window position and size
        :param animate: name of window mover
        :type rectangle: Rectangle
        :type animate: str
        """
        if not animate:
            self.set_position(rectangle)
        else:
            try:
                window_mover = window_movers[animate]
            except KeyError:
                # If the given window mover name isn't found, don't animate.
                self.set_position(rectangle)
            else:
                window_mover.move_window(self, self.get_position(),
                                         rectangle)

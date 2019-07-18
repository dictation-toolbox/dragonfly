# This file is part of Aenea
#
# Aenea is free software: you can redistribute it and/or modify it under
# the terms of version 3 of the GNU Lesser General Public License as
# published by the Free Software Foundation.
#
# Aenea is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with Aenea.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (2014) Alex Roper
# Alex Roper <alex@aroper.net>

# Heavily modified from Aenea's xdotool implementation for X11.

"""
Window class for X11
============================================================================

"""

import logging
from subprocess import Popen, PIPE

import psutil
from six import binary_type

from .base_window import BaseWindow
from .rectangle import Rectangle


class X11Window(BaseWindow):
    """
        The Window class is an interface to the window control and
        placement APIs for X11.

    """

    _log = logging.getLogger("window")

    #-----------------------------------------------------------------------
    # Methods and attributes for running commands.

    # Commands
    xdotool = "xdotool"
    xprop = "xprop"

    @classmethod
    def _run_xdotool_command(cls, arguments, error_on_failure=True):
        return cls._run_command(cls.xdotool, arguments, error_on_failure)

    @classmethod
    def _run_xprop_command(cls, arguments, error_on_failure=True):
        return cls._run_command(cls.xprop, arguments, error_on_failure)

    @classmethod
    def _run_command(cls, command, arguments, error_on_failure=True):
        """
        Run a command with arguments and return the result.

        :param command: command to run
        :type command: str
        :param arguments: arguments to append
        :type arguments: list
        :returns: stdout, stderr, return_code
        :rtype: tuple
        """
        arguments = [str(arg) for arg in arguments]
        full_command = [command] + arguments
        full_readable_command = ' '.join(full_command)
        cls._log.debug(full_readable_command)
        try:
            p = Popen(full_command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()

            # Decode output if it is binary.
            if isinstance(stdout, binary_type):
                stdout = stdout.decode('utf-8')
            if isinstance(stderr, binary_type):
                stderr = stderr.decode('utf-8')

            # Handle non-zero return codes.
            if p.wait() > 0 and error_on_failure:
                print(stdout)
                print(stderr)
                raise RuntimeError("%s command exited with non-zero return"
                                   " code %d" % (command, p.returncode))

            # Return the process output and return code.
            return stdout.rstrip(), stderr.rstrip(), p.returncode
        except Exception as e:
            cls._log.error("Failed to execute command '%s': %s",
                           full_readable_command, e)

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        window_id, _, _ = cls._run_xdotool_command(["getactivewindow"])
        return cls.get_window(int(window_id))

    @classmethod
    def get_all_windows(cls):
        # Get all window IDs using 'xdotool search'.
        output, _, _ = cls._run_xdotool_command(['search', '--onlyvisible',
                                                 '--name', ''])
        lines = [line for line in output.split('\n') if line]
        windows = [cls.get_window(int(line)) for line in lines]

        # Exclude window IDs that have no associated process ID.
        result = []
        for window in windows:
            props = cls._get_properties_from_xprop(window, '_NET_WM_PID')
            if '_NET_WM_PID' not in props:
                continue
            result.append(window)

        return result

    @classmethod
    def get_matching_windows(cls, executable=None, title=None):
        # Get matching window IDs using 'xdotool search'.
        args = ['search', '--onlyvisible', '--name']
        if title:
            args.append(title)
        else:
            args.append('')
        output, _, _ = cls._run_xdotool_command(args, False)
        lines = [line for line in output.split('\n') if line]
        windows = [cls.get_window(int(line)) for line in lines]
        matching = []
        for window in windows:
            if executable:
                if window.executable.lower().find(executable) == -1:
                    continue
            if title:
                if window.title.lower().find(title) == -1:
                    continue
            matching.append(window)

        return matching

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, id):
        super(X11Window, self).__init__(id=id)
        self._pid = -1  # initialized later if required
        self._executable = -1

    def __str__(self):
        args = ["id=%d" % self._id] + list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def _get_properties_from_xprop(self, *properties):
        # This method retrieves windows properties by shelling out to xprop.
        result = {}
        args = ['-id', self.id] + list(properties)
        output, _, return_code = self._run_xprop_command(args, False)
        if return_code > 0:
            return {}

        for line in output.split('\n'):
            line = line.split(' =', 1)
            if len(line) != 2:
                continue

            raw_key, value = line
            raw_key, value = raw_key.strip(), value.strip()
            if 'STRING)' in raw_key:  # This also handles (UTF8_STRING).
                value = value[1:-1]

                # Use a list if there are multiple strings.
                if '", "' in value:
                    value = [string for string in value.split('", "')]

            # Get the key without the property type.
            key = raw_key[0:raw_key.find('(')]
            result[key] = value

        # Split up class and class name.
        if 'WM_CLASS' in result:
            window_class_name, window_class = result.pop('WM_CLASS')
            result['cls_name'] = window_class_name
            result['cls'] = window_class

        # Return the requested properties.
        return result

    def _get_window_text(self):
        # Get the title text.
        args = ['getwindowname', self.id]
        return self._run_xdotool_command(args)[0]

    def _get_class_name(self):
        return (self._get_properties_from_xprop("WM_CLASS")
                .get('cls_name', ''))

    @property
    def cls(self):
        """ Read-only access to the window's class. """
        return (self._get_properties_from_xprop("WM_CLASS")
                .get('cls', ''))

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
        # Set the pid once when it is needed.
        if self._pid == -1:
            p = '_NET_WM_PID'
            pid = self._get_properties_from_xprop(p).get(p)
            if pid:
                pid = int(pid)
            self._pid = pid

        return self._pid

    @property
    def role(self):
        """
        Read-only access to the window's X11 role attribute.

        :returns: role
        :rtype: str
        """
        p = 'WM_WINDOW_ROLE'
        return self._get_properties_from_xprop(p).get(p, '')

    @property
    def type(self):
        """
        Read-only access to the window's X11 type property, if it is set.

        :returns: type
        :rtype: str
        """
        p = '_NET_WM_WINDOW_TYPE'
        return self._get_properties_from_xprop(p).get(p, '')

    @property
    def state(self):
        """
        Read-only access to the X window state.

        Windows can have multiple states, so this returns a tuple.

        This property invokes a (relatively) long-running function, so
        store the result locally instead of using it multiple times.

        If the window does not have the _NET_WM_STATE property, then
        ``None`` will be returned.

        :return: window state (if any)
        :rtype: tuple | None
        """
        p = '_NET_WM_STATE'
        net_wm_state = self._get_properties_from_xprop(p).get(p)
        if net_wm_state is None:
            # Indicate to callers that _NET_WM_STATE was missing.
            return None
        elif not net_wm_state:
            return tuple()
        else:
            return tuple(net_wm_state.split(', '))

    @property
    def _no_window_state(self):
        return self.state is None

    def _get_window_module(self):
        # Get the executable using the process ID and psutil.
        pid = self.pid
        if pid is None:
            self._executable = ''
        elif self._executable == -1:
            for p in psutil.process_iter(attrs=['pid', 'exe']):
                if p.info['pid'] == pid:
                    self._executable = p.info['exe']
                    return self._executable

            # Set to '' if it wasn't found.
            self._executable = ''

        return self._executable

    @classmethod
    def _is_minimized(cls, state):
        return state is not None and '_NET_WM_STATE_HIDDEN' in state

    @property
    def is_minimized(self):
        return self._is_minimized(self.state)

    @property
    def is_visible(self):
        state = self.state
        return state is not None and '_NET_WM_STATE_HIDDEN' not in state

    @classmethod
    def _is_maximized(cls, state):
        # Note: this means a window must be maximized both horizontally and
        # vertically, but that is typically what maximize means anyway.
        return (state is not None and
                '_NET_WM_STATE_MAXIMIZED_VERT' in state and
                '_NET_WM_STATE_MAXIMIZED_HORZ' in state)

    @property
    def is_maximized(self):
        return self._is_maximized(self.state)

    @property
    def is_fullscreen(self):
        """
        Whether the window is in fullscreen mode.

        This does not work for all window types (e.g. pop up menus).

        :rtype: bool
        """
        state = self.state
        return state is not None and '_NET_WM_STATE_FULLSCREEN' in state

    @property
    def is_focused(self):
        """
        Whether the window has input focus.

        This does not work for all window types (e.g. pop up menus).

        :rtype: bool
        """
        state = self.state
        return state is not None and '_NET_WM_STATE_FOCUSED' in state

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        output, _, _ = self._run_xdotool_command(
            ['getwindowgeometry', '--shell', self.id])
        geometry = output.strip().split('\n')
        geo = dict([val.lower()
                    for val in line.split('=')]
                   for line in geometry)
        geo = dict((key, int(value)) for (key, value) in geo.items())
        return Rectangle(geo['x'], geo['y'], geo['width'], geo['height'])

    def set_position(self, rectangle):
        l, t, w, h = rectangle.ltwh
        id = self.id
        self._run_xdotool_command(
            ['windowmove', id, l, t,
             'windowsize', id, w, h])

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        self._run_xdotool_command(['windowminimize', self.id])

    def _toggle_maximize(self):
        # Doesn't seem possible with xdotool. We'll try pressing a-f10
        # with the window focused.
        self.set_foreground()
        self._run_xdotool_command(['keydown', 'Alt_L', 'key', 'F10',
                                   'keyup', 'Alt_L'])

    def maximize(self):
        if not self.is_maximized:
            self._toggle_maximize()

    def restore(self):
        state = self.state
        if self._is_minimized(state):
            self._run_xdotool_command(['windowactivate', self.id])
        elif self._is_maximized(state):
            self._toggle_maximize()

    def set_foreground(self):
        if self.is_minimized:
            self.restore()
        if not self.is_focused:
            id = '%i' % self.id
            self._run_xdotool_command(['windowactivate', id,
                                       'windowfocus', id])

    def set_focus(self):
        """
        Set the input focus to this window.

        This method will set the input focus, but will not necessarily bring
        the window to the front.
        """
        self._run_xdotool_command(['windowfocus', self.id])

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

# pylint: disable=W0622
# Suppress warnings about redefining the built-in 'id' function.

from __future__ import print_function

import locale
import logging
import os
from subprocess import Popen, PIPE
import sys

import psutil
from six import binary_type

from .base_window import BaseWindow
from .rectangle import Rectangle


class X11Window(BaseWindow):
    """
        The Window class is an interface to the window control and
        placement APIs for X11.

        Window control methods such as :meth:`close` will return ``True``
        if successful.

        This class requires the following external programs:

        * ``wmctrl``
        * ``xdotool``
        * ``xprop``

    """

    _log = logging.getLogger("window")

    #-----------------------------------------------------------------------
    # Methods and attributes for running commands.

    # Commands
    wmctrl = "wmctrl"
    xdotool = "xdotool"
    xprop = "xprop"

    @classmethod
    def _run_command(cls, command, arguments):
        """
        Run a command with arguments and return the result.

        :param command: command to run
        :type command: str
        :param arguments: arguments to append
        :type arguments: list
        :returns: stdout, return_code
        :rtype: tuple
        """
        arguments = [str(arg) for arg in arguments]
        full_command = [command] + arguments
        full_readable_command = ' '.join(full_command)
        cls._log.debug(full_readable_command)
        try:
            kwargs = dict(stdout=PIPE, stderr=PIPE)

            # Fork the process with setsid() if on a POSIX system such as
            # Linux.
            if os.name == 'posix':
                kwargs.update(dict(preexec_fn=os.setsid))

            # Execute the child process.
            p = Popen(full_command, **kwargs)
            stdout, stderr = p.communicate()

            # Decode output if it is binary.
            encoding = locale.getpreferredencoding()
            if isinstance(stdout, binary_type):
                stdout = stdout.decode(encoding)
            if isinstance(stderr, binary_type):
                stderr = stderr.decode(encoding)

            # Print error messages to stderr. Filter BadWindow messages.
            stderr = stderr.rstrip()
            if stderr and "BadWindow" not in stderr:
                print(stderr, file=sys.stderr)

            # Return the process output and return code.
            return stdout.rstrip(), p.returncode
        except OSError as e:
            cls._log.error("Failed to execute command '%s': %s. Is "
                           "%s installed?",
                           full_readable_command, e, command)
            raise e

    @classmethod
    def _run_command_simple(cls, exe, arguments):
        # Run the command and return whether or not it succeeded based on
        # the return code.
        stdout, return_code = cls._run_command(exe, arguments)
        if stdout: print(stdout)
        return return_code == 0

    @classmethod
    def _run_wmctrl_command_simple(cls, arguments):
        return cls._run_command_simple(cls.wmctrl, arguments)

    @classmethod
    def _run_xdotool_command(cls, arguments):
        return cls._run_command(cls.xdotool, arguments)

    @classmethod
    def _run_xdotool_command_simple(cls, arguments):
        return cls._run_command_simple(cls.xdotool, arguments)

    @classmethod
    def _run_xprop_command(cls, arguments):
        return cls._run_command(cls.xprop, arguments)

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        window_id, return_code = cls._run_xdotool_command([
            "getactivewindow"
        ])
        if return_code == 0:
            return cls.get_window(int(window_id))
        else:
            return cls.get_window(0)  # return an invalid window

    @classmethod
    def get_all_windows(cls):
        # Get all window IDs using 'xdotool search'.
        stdout, return_code = cls._run_xdotool_command([
            'search', '--onlyvisible', '--name', ''
        ])
        if return_code == 0:
            lines = [line for line in stdout.split('\n') if line]
            windows = [cls.get_window(int(line)) for line in lines]
        else:
            # Return any windows found previously.
            if stdout: print(stdout)
            return list(cls._windows_by_id.values())

        # Exclude window IDs that have no associated process ID.
        result = []
        for window in windows:
            props = cls._get_properties_from_xprop(window, '_NET_WM_PID',
                                                   '_NET_WM_STATE')
            if '_NET_WM_PID' not in props:
                continue
            has_state = '_NET_WM_STATE' not in props
            result.append((window, has_state))

        # Sort the list so that windows without _NET_WM_STATE are
        # last.
        result.sort(key=lambda pair: pair[1])
        return [w for (w, _) in result]  # return just the windows

    @classmethod
    def get_matching_windows(cls, executable=None, title=None):
        # Make window searches case-insensitive.
        if executable:
            executable = executable.lower()
        if title:
            title = title.lower()

        # Get matching window IDs using 'xdotool search'.
        args = ['search', '--onlyvisible', '--name']
        if title:
            args.append(title)
        else:
            args.append('')
        stdout, return_code = cls._run_xdotool_command(args)
        if return_code == 0:
            lines = [line for line in stdout.split('\n') if line]
            windows = [cls.get_window(int(line)) for line in lines]
        else:
            # Use windows found previously.
            if stdout: print(stdout)
            windows = list(cls._windows_by_id.values())

        matching = []
        for window in windows:
            if executable:
                if window.executable.lower().find(executable) == -1:
                    continue
            if title:
                if window.title.lower().find(title) == -1:
                    continue

            # Match found.
            matching.append(window)

        # Sort the window list so that windows without _NET_WM_STATE are
        # last.
        matching.sort(key=lambda w: w.state is None)
        return matching

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, id):
        super(X11Window, self).__init__(id=id)
        self._pid = -1  # initialized later if required
        self._executable = -1

    def __repr__(self):
        args = ["id=%d" % self._id] + list(self._names)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def _get_properties_from_xprop(self, *properties):
        # This method retrieves windows properties by shelling out to xprop.
        result = {}
        args = ['-id', self.id] + list(properties)
        stdout, return_code = self._run_xprop_command(args)
        if return_code > 0:
            return {}

        for line in stdout.split('\n'):
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
        stdout, return_code = self._run_xdotool_command(args)
        if return_code == 0:
            return stdout
        else:
            if stdout: print(stdout)
            return ""

    def _get_class_name(self):
        return (self._get_properties_from_xprop("WM_CLASS")
                .get('cls_name', ''))

    def _get_window_pid(self):
        # Set the pid once when it is needed.
        if self._pid == -1:
            p = '_NET_WM_PID'
            pid = self._get_properties_from_xprop(p).get(p)
            if pid:
                pid = int(pid)
            self._pid = pid

        return self._pid

    @property
    def cls(self):
        """ Read-only access to the window's class. """
        return (self._get_properties_from_xprop("WM_CLASS")
                .get('cls', ''))

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
        if pid == -1:
            self._executable = ''
        elif self._executable == -1:
            for p in psutil.process_iter(attrs=['pid', 'exe', 'name']):
                if p.info['pid'] == pid:
                    self._executable = p.info['exe'] or p.info['name']
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
        stdout, return_code = self._run_xdotool_command(
            ['getwindowgeometry', '--shell', self.id])
        if return_code > 0:
            if stdout: print(stdout)
            return Rectangle(0, 0, 0, 0)

        geometry = stdout.strip().split('\n')
        geo = dict([val.lower()
                    for val in line.split('=')]
                   for line in geometry)
        geo = dict((key, int(value)) for (key, value) in geo.items())
        return Rectangle(geo['x'], geo['y'], geo['width'], geo['height'])

    def set_position(self, rectangle):
        l, t, w, h = rectangle.ltwh
        id = self.id
        return self._run_xdotool_command_simple(
            ['windowmove', id, l, t,
             'windowsize', id, w, h]
        )

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        # Attempt to minimize the window. Return the command's success.
        return self._run_xdotool_command_simple(['windowminimize',
                                                 self.id])

    def _toggle_maximize(self, is_maximized):
        # Use wmctrl to add or remove the maximized window properties from
        # the window's _NET_WM_STATE set.
        # Note: this should be possible with xprop, but is not supported.
        maximized_props = 'maximized_vert,maximized_horz'
        add_remove = 'remove' if is_maximized else 'add'
        return self._run_wmctrl_command_simple([
            '-ir', self.id, '-b', '%s,%s' % (add_remove, maximized_props)
        ])

    def maximize(self):
        if not self.is_maximized:
            return self._toggle_maximize(False)
        return True  # already maximized.

    def restore(self):
        state = self.state
        if self._is_minimized(state):
            return self._run_xdotool_command_simple([
                'windowactivate', self.id
            ])
        elif self._is_maximized(state):
            return self._toggle_maximize(True)
        else:
            # True if already restored or False if no _NET_WM_STATE.
            return state is not None

    def close(self):
        return self._run_xdotool_command_simple(['windowclose', self.id])

    def set_foreground(self):
        # Restore if minimized.
        if self.is_minimized and not self.restore():
            return False  # restore() failed
        if not self.is_focused:
            id = '%i' % self.id
            return self._run_xdotool_command_simple([
                'windowactivate', id, 'windowfocus', id
            ])

        return True

    def set_focus(self):
        """
        Set the input focus to this window.

        This method will set the input focus, but will not necessarily bring
        the window to the front.
        """
        return self._run_xdotool_command_simple([
            'windowfocus', self.id
        ])

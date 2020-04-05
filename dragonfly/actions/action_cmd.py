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
RunCommand action
============================================================================

The :class:`RunCommand` action takes a command-line program to run including
any required arguments. On execution, the program will be started as a
subprocess.

Processing will occur asynchronously by default. Commands running
asynchronously should not normally prevent the Python process from exiting.

It may sometimes be necessary to use a list for the action's *command*
argument instead of a string. This is because some command-line shells may
not work 100% correctly with Python's built-in :meth:`shlex.split` function.

This action should work on Windows and other platforms.

Example using the ping command::

    from dragonfly import RunCommand

    # Ping localhost for 4 seconds.
    RunCommand('ping -w 4 localhost').execute()


Example using a command list instead of a string::

    from dragonfly import RunCommand

    # Ping localhost for 4 seconds.
    RunCommand(['ping', '-w', '4', 'localhost']).execute()


Example using the optional function parameter::

    from __future__ import print_function
    from locale import getpreferredencoding
    from six import binary_type
    from dragonfly import RunCommand

    def func(proc):
        # Read lines from the process.
        encoding = getpreferredencoding()
        for line in iter(proc.stdout.readline, b''):
            if isinstance(line, binary_type):
                line = line.decode(encoding)
            print(line, end='')

    RunCommand('ping -w 4 localhost', func).execute()


Example using the optional synchronous parameter::

    from dragonfly import RunCommand

    RunCommand('ping -w 4 localhost', synchronous=True).execute()


Example using the optional hide_window parameter::

    from dragonfly import RunCommand

    # Use hide_window=False for running GUI applications via RunCommand.
    RunCommand('notepad.exe', hide_window=False).execute()


Example using the subprocess's :class:`Popen` object::

    from dragonfly import RunCommand

    # Initialise and execute a command asynchronously.
    cmd = RunCommand('ping -w 4 localhost')
    cmd.execute()

    # Wait until the subprocess finishes.
    cmd.process.wait()


Example using a subclass::

    from __future__ import print_function
    from locale import getpreferredencoding
    from six import binary_type
    from dragonfly import RunCommand

    class Ping(RunCommand):
        command = "ping -w 4 localhost"
        synchronous = True
        def process_command(self, proc):
            # Read lines from the process.
            encoding = getpreferredencoding()
            for line in iter(proc.stdout.readline, b''):
                if isinstance(line, binary_type):
                    line = line.decode(encoding)
                print(line, end='')

    Ping().execute()


Class reference
----------------------------------------------------------------------------

"""

from __future__ import print_function

import locale
import os
import shlex
import subprocess
import threading

from six import string_types, binary_type

from .action_base import ActionBase

# --------------------------------------------------------------------------


class RunCommand(ActionBase):
    """
        Start an application from the command-line.

        This class is similar to the :class:`StartApp` class, but is
        designed for running command-line applications and optionally
        processing subprocesses.

    """
    command = None
    synchronous = False

    def __init__(self, command=None, process_command=None,
                 synchronous=False, hide_window=True):
        """
            Constructor arguments:
             - *command* (str or list) -- the command to run when this
               action is executed. It will be parsed by :meth:`shlex.split`
               if it is a string and passed directly to ``subprocess.Popen``
               if it is a list. Command arguments can be included.
             - *process_command* (callable) -- optional callable to invoke
               with the :class:`Popen` object after successfully starting
               the subprocess. Using this argument overrides the
               :meth:`process_command` method.
             - *synchronous* (bool, default *False*) -- whether to wait
               until :meth:`process_command` has finished executing before
               continuing.
             - *hide_window* (bool, default *True*) -- whether to hide the
               application window. Set to *False* if using this action with
               GUI programs. This argument only applies to Windows. It has
               no effect on other platforms.

        """
        ActionBase.__init__(self)
        self._proc = None

        # Complex handling of arguments because of clashing use of the names
        # at the class level: property & class-value.
        if command is not None:
            self.command = command
        command_types = (string_types, list)
        if not (self.command and isinstance(self.command, command_types)):
            raise TypeError("command must be a non-empty string or list, "
                            "not %s" % self.command)
        if synchronous is not False:
            self.synchronous = synchronous

        if not (process_command is None or callable(process_command)):
            raise TypeError("process_command must be a callable object or "
                            "None")

        self._process_command = process_command
        self._hide_window = hide_window

        # Set the string used for representing actions.
        if isinstance(self.command, list):
            self._str = "'%s'" % " ".join(self.command)
        else:
            self._str = "'%s'" % self.command

    @property
    def process(self):
        """
            The :class:`Popen` object for the current subprocess if one has
            been started, otherwise ``None``.
        """
        return self._proc

    # pylint: disable=no-self-use
    def process_command(self, proc):
        """
            Method to override for custom handling of the command's
            :class:`Popen` object.

            By default this method prints lines from the subprocess until it
            exits.
        """
        encoding = locale.getpreferredencoding()
        for line in iter(proc.stdout.readline, b''):
            if isinstance(line, binary_type):
                line = line.decode(encoding)

            print(line, end='')

    def _execute(self, data=None):
        self._log.info("Executing: %s", self.command)

        # Suppress showing the new CMD.exe window on Windows.
        startupinfo = None
        if os.name == 'nt' and self._hide_window:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Pre-process self.command before passing it to subprocess.Popen.
        command = self.command
        if isinstance(command, string_types):
            # Split command strings using shlex before passing it to Popen.
            # Use POSIX mode only if on a POSIX platform.
            command = shlex.split(command, posix=os.name == "posix")
        try:
            self._proc = subprocess.Popen(command,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          stdin=subprocess.PIPE,
                                          startupinfo=startupinfo)
        except Exception as e:
            self._log.exception("Exception from starting subprocess %s: "
                                "%s", self._str, e)
            return False

        # Call process_command either synchronously or asynchronously.
        def call():
            try:
                if self._process_command:
                    process_func = self._process_command
                else:
                    process_func = self.process_command
                process_func(self._proc)
                return_code = self._proc.wait()
                if return_code != 0:
                    self._log.error("Command %s failed with return code "
                                    "%d", self._str, return_code)
                    return False
                return True
            except Exception as e:
                self._log.exception("Exception processing command %s: %s",
                                    self._str, e)
                return False
            finally:
                self._proc = None

        if self.synchronous:
            return call()

        # Execute in a new daemonized thread so that the command cannot
        # stop the SR engine from exiting.
        thread = threading.Thread(target=call)
        thread.setDaemon(True)
        thread.start()
        return True

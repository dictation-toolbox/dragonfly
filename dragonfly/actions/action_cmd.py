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

This action should work correctly on Windows and other platforms.

Example using the optional function parameter::

    from dragonfly import RunCommand

    def func(proc):
        # Read lines from the process.
        for line in iter(proc.stdout.readline, b''):
            print(line)

    RunCommand('ping localhost', func).execute()


Example using a subclass::

    from dragonfly import RunCommand

    class Ping(RunCommand):
        command = "ping localhost"
        def process_command(self, proc):
            # Read lines from the process.
            for line in iter(proc.stdout.readline, b''):
                print(line)

    Ping().execute()


Class reference
----------------------------------------------------------------------------

"""

import os
import shlex
import subprocess

from six import string_types

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

    def __init__(self, command=None, process_command=None):
        """
            Constructor arguments:
             - *command* (str) -- the command to run when this action is
               executed. The command may include arguments and will be
               parsed by :meth:`shlex.split`.
             - *process_command* (callable) -- optional callable to invoke
               with the :class:`Popen` object after successfully starting
               the subprocess. Using this argument effectively overrides
               the :meth:`process_command` method.

        """
        ActionBase.__init__(self)

        # Complex handling of arguments because of clashing use of the names
        # at the class level: property & class-value.
        if command is not None:
            self.command = command
        if not (self.command and isinstance(self.command, string_types)):
            raise TypeError("command must be a non-empty string, not %s"
                            % self.command)
        if callable(process_command):
            self.process_command = process_command
        if not callable(self.process_command):
            raise TypeError("process_command must be a callable object or None")

    def process_command(self, proc):
        """
        Virtual method to override for custom handling of the command's
        :class:`Popen` object.
        """

    def _execute(self, data=None):
        self._log.info("Executing: %s" % self.command)

        # Suppress showing the new CMD.exe window on Windows.
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            proc = subprocess.Popen(shlex.split(self.command),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE,
                                    startupinfo=startupinfo)
        except Exception as e:
            self._log.exception("Exception from starting subprocess %s: %s"
                                % (self.command, e))
            return False

        self.process_command(proc)

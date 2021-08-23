# This file was part of Aenea
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

# This keyboard implementation is based on Aenea's x11_xdotool.py file.

import logging
import os
import subprocess

from ._x11_base import BaseX11Keyboard, KEY_TRANSLATION


class XdotoolKeyboard(BaseX11Keyboard):
    """Static class for typing keys with xdotool."""

    _log = logging.getLogger("keyboard")

    # xdotool command
    xdotool = "xdotool"

    @classmethod
    def send_keyboard_events(cls, events):
        """
        Send a sequence of keyboard events.

        Positional arguments:
        events -- a sequence of tuples of the form
            (keycode, down, timeout), where
                keycode (str): key symbol.
                down (boolean): True means the key will be pressed down,
                    False means the key will be released.
                timeout (float): number of seconds to sleep after
                    the keyboard event.

        """
        cls._log.debug("Keyboard.send_keyboard_events %r", events)

        # Return early if there are no events (e.g. for Key("")).
        if not events:
            return

        arguments = []
        for event in events:
            (key, down, timeout) = event
            key = KEY_TRANSLATION.get(key, key)

            # Add arguments for pressing keys.
            if down:
                arguments += ['keydown', '--delay', '0', key]
            else:
                arguments += ['keyup', '--delay', '0', key]

            # Instruct xdotool to sleep after the keyboard event if
            # necessary.
            if timeout:
                arguments += ['sleep', '%.3f' % timeout]

        # Press/release the keys using xdotool, catching any errors.
        command = [cls.xdotool] + arguments
        readable_command = ' '.join(command)
        cls._log.debug(readable_command)
        try:
            # Fork the process with setsid() if on a POSIX system such as
            # Linux.
            kwargs = {}
            if os.name == 'posix':
                kwargs.update(dict(preexec_fn=os.setsid))

            # Execute the xdotool child process.
            p = subprocess.Popen(command, **kwargs)
            if p.wait() > 0:
                raise RuntimeError("xdotool command exited with non-zero "
                                   "return code %d" % p.returncode)
        except Exception as e:
            cls._log.exception("Failed to execute xdotool command '%s': "
                               "%s", readable_command, e)

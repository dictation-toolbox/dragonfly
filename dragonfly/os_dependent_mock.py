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

"""
Mock module to allow dragonfly to be imported on linux locally.
Heavily modified to allow more dragonfly functionality to work
regardless of operating system.
"""


class _WindowInfo(object):
    executable = None
    title = None
    handle = None


class Window(object):
    @staticmethod
    def get_foreground():
        return _WindowInfo


class COMError(Exception):
    pass


class Dispatch(object):
    def __init__(self, app_name):
        pass


class Clipboard:
    pass


class ConnectionGrammar:
    pass


class FocusWindow:
    pass


class HardwareInput:
    pass


class Key:
    pass


class Keyboard:
    pass


class KeyboardInput:
    pass


monitors = []


class Monitor:
    pass


class Mouse:
    pass


class MouseInput:
    pass


class Paste:
    pass


class Text:
    pass


class Typeable:
    pass


typeables = {}

def make_input_array(inputs):
    pass


def send_input_array(input_array):
    pass


class WaitWindow:
    pass


class Word:
    pass


class StartApp:
    pass


class BringApp:
    pass


class PlaySound:
    pass

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
from .actions import ActionBase, DynStrActionBase


# Mock ActionBase and DynStrActionBase classes

def mock_action(*args, **kwargs):
    return ActionBase()


def mock_dyn_str_action(*args, **kwargs):
    return DynStrActionBase(*args, **kwargs)

Text = mock_dyn_str_action
Key = mock_dyn_str_action
Mouse = mock_dyn_str_action
Paste = mock_dyn_str_action
WaitWindow = mock_action
FocusWindow = mock_action
StartApp = mock_action
BringApp = mock_action
PlaySound = mock_action


class _WindowInfo(object):
    # TODO Use proxy contexts instead
    executable = ""
    title = ""
    handle = ""


class Window(object):
    @staticmethod
    def get_foreground():
        return _WindowInfo


class MockBase(object):
    def __init__(self, *args, **kwargs):
        pass


class HardwareInput(MockBase):
    pass


class Keyboard(MockBase):
    pass


class KeyboardInput(MockBase):
    pass


monitors = []


class Monitor(MockBase):
    pass


class MouseInput(MockBase):
    pass


class Typeable(object):
    pass

typeables = {}


def make_input_array(inputs):
    return inputs


def send_input_array(input_array):
    pass

#
# This file is part of Dragonfly.
# (c) Copyright 2021 by Dane Finlay
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
    This module demonstrates Dragonfly's window movement functionality.  A
    number of classes are employed to demo a good number of use cases with a
    smaller amount of code.

    This module can be activated in the same way as other Natlink macros
    by placing it in the "NatLink/MacroSystem" folder or in a folder loaded
    by one of Dragonfly's module loaders.

"""

# pylint: disable=invalid-name

from dragonfly import Grammar, CompoundRule, Compound, Window
from dragonfly.actions.mouse import  get_cursor_position


#---------------------------------------------------------------------------
# Create this module's grammar.

grammar = Grammar("Window move example")


#---------------------------------------------------------------------------
# Define classes for window movement.

class WindowMovementBase:
    """
        Base class for moving a target window.
    """

    def __init__(self):
        self.target_window = None

    def target_foreground_window(self):
        """
            Set the target window to the current foreground window.
        """
        self.target_window = Window.get_foreground()

    def move_target_window(self, window_animation):
        """
            Move the window, animating the movement of the window if
            specified.
        """
        target_window = self.target_window
        src_pos = target_window.get_position()
        dst_pos = self.calculate_target_window_destination(src_pos)
        target_window.move(dst_pos, window_animation)

    def calculate_target_window_destination(self, src_position):
        """
            Calculate and return the target window destination.

            This method should be overridden to return a Rectangle
            object representing where the window should be moved.
        """
        raise NotImplementedError()


class MoveWindowHere(WindowMovementBase):
    """
        Class for moving a target window to the current cursor position.
    """

    def calculate_target_window_destination(self, src_position):
        # The destination of the target window is the source position with
        #  its top left-hand corner at the current cursor position.
        x_mouse, y_mouse = get_cursor_position()
        src_position.x1 = x_mouse
        src_position.y1 = y_mouse
        return src_position


class CenterWindowHere(WindowMovementBase):
    """
        Class for centering a target window on the current cursor position.
    """

    def calculate_target_window_destination(self, src_position):
        # The destination of the target window is the source position
        #  centered on the current cursor position.
        x_mouse, y_mouse = get_cursor_position()
        relative_x_center = src_position.x_center - src_position.x1
        relative_y_center = src_position.y_center - src_position.y1
        src_position.x1 = x_mouse - relative_x_center
        src_position.y1 = y_mouse - relative_y_center
        return src_position


#---------------------------------------------------------------------------
# Define rule classes for window movement rules.

class MoveWindowRule(CompoundRule):
    """
        Base class for window movement rules.
    """

    #: The extra to use for optionally animating window movement.
    window_animation_extra_name = "animation"

    #-----------------------------------------------------------------------

    def __init__(self, window_movement, name=None, spec=None, extras=None,
                 defaults=None, exported=None, context=None):
        # pylint: disable=too-many-arguments
        CompoundRule.__init__(self, name, spec, extras, defaults, exported,
                              context)
        self.window_movement = window_movement

    #-----------------------------------------------------------------------

    def move_target_window(self, extras):
        """
            Move the target window.
        """
        # Get the value for the window animation extra (or None) and move
        #  the target window, passing the value.
        window_animation = extras.get(self.window_animation_extra_name)
        self.window_movement.move_target_window(window_animation)


class MoveForegroundWindowRule(MoveWindowRule):
    """
        Class for foreground window movement rules.
    """

    def _process_recognition(self, node, extras):
        # Set the foreground window as the target window and move it.
        self.window_movement.target_foreground_window()
        self.move_target_window(extras)


class MoveNotepadWindowRule(MoveWindowRule):
    """
        Class for notepad window movement rules.
    """

    def _process_recognition(self, node, extras):
        # Find a notepad window, set it as the target window and move it.
        #  Display a warning if no notepad window was found.
        notepad_windows = Window.get_matching_windows(executable="notepad",
                                                      title="notepad")
        if not notepad_windows:
            print("Could not find a notepad window to move.")
            return

        self.window_movement.target_window = notepad_windows[0]
        self.move_target_window(extras)


#---------------------------------------------------------------------------
# Create window movement objects to be used by our window movement rules.
move_window_here = MoveWindowHere()
center_window_here = CenterWindowHere()

# Define common extras for movement rules: an <animation> extra for
#  optionally animating window movement.
common_extras = [
    Compound(
        spec="animated", name="animation",

        # Possible window animation values: "linear", "spline".
        value_func=lambda _, __: "spline"
    )
]

# Create a rule for moving the foreground window to the current cursor
#  position.
rule1 = MoveForegroundWindowRule(
    window_movement=move_window_here,
    name="rule1",
    spec="move [this] window here [<animation>]",
    extras=common_extras
)

# Create a rule for centering the foreground window on the current cursor
#  position.
rule2 = MoveForegroundWindowRule(
    window_movement=center_window_here,
    name="rule2",
    spec="center [this] window here [<animation>]",
    extras=common_extras
)

# Create a rule for moving a notepad window to the current cursor position.
rule3 = MoveNotepadWindowRule(
    window_movement=move_window_here,
    name="rule3",
    spec="move notepad [window] here [<animation>]",
    extras=common_extras
)

# Create a rule for centering a notepad window on the current cursor
#  position.
rule4 = MoveNotepadWindowRule(
    window_movement=center_window_here,
    name="rule4",
    spec="center notepad [window] here [<animation>]",
    extras=common_extras
)

# Add our rules to the grammar instance.
grammar.add_rule(rule1)
grammar.add_rule(rule2)
grammar.add_rule(rule3)
grammar.add_rule(rule4)


#---------------------------------------------------------------------------
# Load the grammar instance and define how to unload it.

grammar.load()

# Unload function which will be called by natlink at unload time.
def unload():
    global grammar
    if grammar:
        grammar.unload()
    grammar = None

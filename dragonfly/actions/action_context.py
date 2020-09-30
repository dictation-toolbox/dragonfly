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


'''
ContextAction
============================================================================

'''


from .action_base import ActionBase
from ..grammar.context import Context
from ..windows import Window


def _ensure_execution_context(data):
    '''Populates the data field of execute with context information if
    not present.'''
    if data is None:
        data = {}
    if '_context' not in data:
        data['_context'] = Window.get_foreground()
    return data

class ContextAction(ActionBase):
    '''
    Action class to execute a different action depending on which context is
    currently active.

    This is especially useful for allowing the same commands to work in
    multiple applications without redefining them in other grammars. An
    example of this is the redo shortcut. Some applications use
    *Ctrl+Shift+Z*, while others might use *Ctrl+Y* instead.
    ``ContextAction`` could be used to define *Ctrl+Y* as the default and
    use *Ctrl+Shift+Z* for specific contexts::

        redo = ContextAction(default=Key('c-y'), actions=[
            # Use cs-z for rstudio
            (AppContext(executable="rstudio"), Key('cs-z')),
        ])

    This class was originally written for the
    `Aenea <https://github.com/dictation-toolbox/aenea>`__ project by Alex
    Roper and has been modified to work without Aenea's functionality.
    '''
    def __init__(self, default=None, actions=None):
        '''
            Constructor arguments:
             - *default* (action object, default *do nothing*) -- the
               default action to execute if there was no matching context in
               *actions*.
             - *actions* (iterable, default *empty list*) -- an iterable
               object containing context-action pairs. The action of the
               first matching context will be executed.

        '''
        if actions is None:
            actions = []

        # Validate default action.
        # Use a new ActionBase action (to do nothing) if default is None.
        if default is None:
            self._log_init.debug("Using default action for ContextAction")
            default = ActionBase()

        # Otherwise check if default is an action.
        elif not isinstance(default, ActionBase):
            raise TypeError("Default action for ContextAction should be an "
                            "ActionBase or None, not %s." % default)

        # Set the default action.
        self.default = default

        # Validate the actions list.
        # Check if it can be converted to a dictionary. or convert it to a
        # is one already (for consistent evaluation order).
        if not isinstance(actions, dict):
            dict(actions)  # can raise a ValueError

        # Convert dictionaries to lists instead for consistent evaluation
        # order.
        else:
            actions = list(actions.items())

        # Check the types of all keys and values.
        for (context, action) in actions:
            if not isinstance(context, Context):
                raise TypeError("ContextAction actions list contains "
                                "unexpected object: %s, instead of a "
                                "Context." % context)
            if not isinstance(action, ActionBase):
                raise TypeError("ContextAction actions list contains "
                                "unexpected object: %s, instead of an "
                                "ActionBase." % action)

        # Set the actions list.
        self.actions = actions
        ActionBase.__init__(self)

    def add_context(self, context, action):
        '''
        Add a context-action pair to the *actions* list.

        :param context: dragonfly context
        :param action: dragonfly action
        :type context: Context
        :type action: ActionBase
        '''
        self.actions.append((context, action))

    def _execute(self, data=None):
        data = _ensure_execution_context(data)
        win = data['_context']
        try:
            for (context, action) in self.actions:
                if context.matches(win.executable, win.title, win.handle):
                    return action.execute(data)

            # Execute the default action and return the success.
            return self.default.execute(data)
        except Exception as e:
            self._log.exception("Exception from matching context or "
                                "executing action %s: %s", self._str, e)
            return False

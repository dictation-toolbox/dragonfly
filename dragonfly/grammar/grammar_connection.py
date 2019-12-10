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
    This file implements the ConnectionGrammar class.
"""

# pylint: disable=expression-not-assigned

from six import string_types

try:
    from win32com.client import Dispatch
    from pywintypes import com_error
except ImportError as error:
    import sys
    if sys.platform.startswith("win"):
        raise error

    # These modules aren't available on non-Windows platforms, so mock what is used.
    class COMError(Exception):
        pass

    com_error = COMError

    class Dispatch(object):
        def __init__(self, _):
            pass

from .grammar_base import Grammar


# ---------------------------------------------------------------------------

class ConnectionGrammar(Grammar):
    """
        Grammar class for maintaining a COM connection well
        within a given context.  This is useful for controlling
        applications through COM while they are in the
        foreground.  This grammar class will take care of
        dispatching the correct COM interface when the
        application comes to the foreground, and releasing it
        when the application is no longer there.

         * ``name`` -- name of this grammar.
         * ``description`` -- description for this grammar.
         * ``context`` -- context within which to maintain
           the COM connection.
         * ``app_name`` -- COM name to dispatch.
    """

    def __init__(self, name, description=None, context=None, app_name=None):
        assert isinstance(app_name, string_types) or app_name is None
        self._app_name = app_name
        self._application = None
        Grammar.__init__(self, name=name, description=description,
                         context=context)

    def __del__(self):
        try:
            self.disconnect()
        except Exception as e:
            self._log.warning("Grammar %s: failed to disconnect from "
                              "%r: %s.", self, self._app_name, e)

    # -----------------------------------------------------------------------
    # Methods for context management.

    application = property(lambda self: self._application,
                           doc="COM handle to the application.")

    def enter_context(self):
        if self.connect():
            self.connection_up()
            return True
        else:
            return False

    def exit_context(self):
        [r.deactivate() for r in self._rules if r.active]
        self.disconnect()
        self.connection_down()

    def _process_begin(self, executable, title, handle):
        # If not connected yet, retry.  If the connection fails after
        #  single attempt, give up.
        if not self._application:
            if not self.connect():
                return False
            self.connection_up()
        return True

    # -----------------------------------------------------------------------
    # Methods for managing the application connection.

    def connect(self):
        if not self._app_name:
            return True
        try:
            self._application = Dispatch(self._app_name)
        except com_error as e:
            if self._log_begin:
                self._log_begin.warning("Grammar %s: failed to connect to "
                                        "%r: %s.", self, self._app_name, e)
            return False
        else:
            [r.activate() for r in self._rules if not r.active]
            return True

    def disconnect(self):
        self._application = None

    def connection_up(self):
        """
            Method called immediately after entering this
            instance's context and successfully setting up its
            connection.

            By default this method doesn't do anything.
            This method should be overridden by derived classes
            if they need to synchronize some internal state with
            the application.  The COM connection is available
            through the ``self.application`` attribute.
        """

    def connection_down(self):
        """
            Method called immediately after exiting this
            instance's context and disconnecting from the
            application.

            By default this method doesn't do anything.
            This method should be overridden by derived classes
            if they need to clean up after disconnection.
        """

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
StartApp action
============================================================================

The :class:`StartApp` action class can be used to start an application by 
running an executable file.


Example usage
----------------------------------------------------------------------------

The following example starts Notepad: ::

   StartApp(r"C:\Windows\system32\\notepad.exe").execute()

Note that the path to *notepad.exe* given above might not be correct for 
your computer, since it depends on the operating system and its 
configuration.


Class reference
----------------------------------------------------------------------------

"""

import os.path
from subprocess    import Popen
from .action_base  import ActionBase, ActionError


#---------------------------------------------------------------------------

class StartApp(ActionBase):
    """
        Start an application.

        This action can be used to run a file (executable), optionally 
        with commandline arguments.

    """

    def __init__(self, *args, **kwargs):
        """
            Constructor arguments:
             - *args* (variable argument list of *str*'s) --
               these strings are passed to subprocess.Popen()
               to start the application as a child process
             - *cwd* (*str*, default *None*) --
               if not *None*, then start the application in this
               directory
    
        """
        ActionBase.__init__(self)
        self._args = args

        if "cwd" in kwargs:  self._cwd = kwargs.pop("cwd")
        else:                self._cwd = None
        if kwargs:
            raise ArgumentError("Invalid keyword arguments: %r" % kwargs)

        # Expand any variables within path names.
        self._args = [self._interpret(a) for a in self._args]
        if self._cwd:
            self._cwd = self._interpret(self._cwd)

        self._str = str(", ".join(repr(a) for a in self._args))

    def _interpret(self, path):
        return os.path.expanduser(os.path.expandvars(path))

    def _execute(self, data=None):
        self._log.debug("Starting app: %r" % (self._args,))
        try:
            Popen(self._args, cwd=self._cwd)
        except Exception, e:
            raise ActionError("Failed to start app %s: %s" % (self._str, e))

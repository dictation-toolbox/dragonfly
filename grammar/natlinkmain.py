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


import sys
import imp
import time
import os.path
import natlink

import dragonfly.grammar.grammar as grammar_
log_ = None


#===========================================================================
# Director class definition.

class Director(object):

    #-----------------------------------------------------------------------
    # Initialization and introspection methods.

    def __init__(self):
        self._log_init  = log_.get_log("director.init")
        self._log_cb    = log_.get_log("director.cb")
        self._log_mod   = log_.get_log("director.mod")

        if self._log_init: self._log_init.debug("Initializing Director.")
        self._modules = {}
        self._mod_dirs = [os.path.expanduser("~/My Documents/natlink")]

    def __str__(self):
        return "%s()" % (self.__class__.__name__)

    def load_modules(self):

        # Check already loaded modules.
        for location, module in self._modules.items():
            if module.has_been_removed():
                if self._log_mod: self._log_mod.debug(
                        "Removing deleted module %s." % module)
                del self._modules[location]
                del module
            elif module.has_been_modified():
                if self._log_mod: self._log_mod.debug(
                        "Reloading modified module %s." % module)
                module.reload()

        # Search for newly added modules.
        for directory in self._mod_dirs:
            directory = os.path.abspath(directory)
            if self._log_mod: self._log_mod.debug(
                    "Loading directory %r." % directory)
            names = self._list_modules(directory)

            for name in names:
                location = (directory, name)
                if location in self._modules: continue

                module = Module(directory, name)
                self._modules[location] = module

                module.load()

    #-----------------------------------------------------------------------
    # Module loading methods.

    def _list_modules(self, directory):
        extension = ".py"
        try:
            pairs = [os.path.splitext(f) for f in os.listdir(directory)
                     if f.endswith(extension)]
        except Exception, e:
            if self._log_mod: self._log_mod.error(
                                "Failed to list modules in directory %r: %s"
                                % (directory, e))
            return None

        # Build the list of module names.
        names = [n for n, e in pairs]
        return names

    #-----------------------------------------------------------------------
    # Recognition-related methods.

    def begin_callback(self, module_info):
        if self._log_cb: self._log_cb.debug("Received begin callback.")

    def change_callback(self, type, arguments):
        if self._log_cb: self._log_cb.debug("Received change callback.")


#===========================================================================
# Module class definition.

class Module(object):

    #-----------------------------------------------------------------------
    # Initialization and introspection methods.

    def __init__(self, directory, name):
        self._log_mod   = log_.get_log("director.mod")

        self._directory = directory
        self._name = name
        self._path = None
        self._load_time = 0
        self._module = None
        self._grammars = []

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._name)

    def has_been_modified(self):
        if not self._path: return False
        try: modify_time = os.path.getmtime(self._path)
        except OSError: return False
        return modify_time > self._load_time

    def has_been_removed(self):
        if not self._path: return False
        return not os.path.exists(self._path)

    def load(self):
        self.load_module()
        self.load_grammars()

    def unload(self):
        self.unload_grammars()
        self.unload_module()

    def reload(self):
        self.unload()
        self.load()

    def load_module(self):
        if self._log_mod: self._log_mod.debug(
                "Loading module %r." % self._name)

        # Attempt to find the requested module.
        try: result = imp.find_module(self._name, [self._directory])
        except ImportError, e:
            if self._log_mod: self._log_mod.error(
                    "Failed to import %r from directory %r: %s"
                    % (self._name, self._directory, e))
            return None

        # Inspect the results from find_module().
        file, path, description = result
        filename = ""

        # Attempt to actually load the requested module.
        try:
            try: module = imp.load_module(self._name, file, filename, description)
            finally: file.close()
        except ImportError, e:
            if self._log_mod: self._log_mod.error(
                    "Failed to load module from %r: %s" % (self._path, e))
            if self._name in sys.modules: del sys.modules[self._name]
            return None
        except Exception, e:
            if self._log_mod: self._log_mod.error(
                    "Exception during init of module %r: %s"
                    % (self._name, e))
            if self._name in sys.modules: del sys.modules[self._name]
            return None
        self._path = path

        # Get and store the module file's modification time.
        try: self._load_time = os.path.getmtime(self._path)
        except OSError:
            if self._log_mod: self._log_mod.error(
                    "Failed to get file modification time for module %r."
                    % self._path)
            if self._name in sys.modules: del sys.modules[self._name]
            return None
        if self._log_mod: self._log_mod.debug(
                "Loaded module from %r (mtime %s)."
                % (self._path, time.ctime(self._load_time)))

        # Store the newly loaded module.
        self._module = module

        # Look for dragonfly grammars in the module.
        self._grammars = []
        for key, value in self._module.__dict__.items():
            if isinstance(value, grammar_.Grammar):
                self._grammars.append(value)
        if self._grammars and self._log_mod: self._log_mod.debug(
                "Found grammars in module %r: %s."
                % (self._name, ", ".join([str(g) for g in self._grammars])))
        if self._log_mod: self._log_mod.debug(
                "System modules %r." % sys.modules)

    def unload_module(self):
        if self._log_mod: self._log_mod.debug(
                "Unloading module %r." % self._name)

        del sys.modules[self._module.__name__]
        del self._module

    def load_grammars(self):
        for grammar in self._grammars:
            try: grammar.load()
            except Exception, e:
                if self._log_mod: self._log_mod.error(
                        "Exception during loading of grammar %s.%s: %s"
                        % (self._name, grammar.name, e))

    def unload_grammars(self):
        for grammar in self._grammars:
            try: grammar.unload()
            except Exception, e:
                if self._log_mod: self._log_mod.error(
                        "Exception during unloading of grammar %s.%s: %s"
                        % (self._name, grammar.name, e))


#===========================================================================
# Stdout and stderr redirection to natlink log window.

class DisplayStream(object):

    def __init__(self, error):
        assert error in (0, 1)
        self._error = error

    def write(self, text):
        natlink.displayText(text, self._error)

    def flush(self):
        pass


def redirect_std_streams():
    sys.stdout = DisplayStream(0)
    sys.stderr = DisplayStream(1)


#===========================================================================
# Main initialization control code.

def initialize():

    # Redirect standard output and standard error to the
    #  natlink-controlled no save file log window.
    redirect_std_streams()
    import dragonfly.log as log
    global log_; log_ = log

    director = Director()
    director.load_modules()

    natlink.setBeginCallback(director.begin_callback)
    natlink.setChangeCallback(director.change_callback)


initialize()

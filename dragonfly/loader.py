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
Command module loading classes
============================================================================

"""

import logging
import os.path
import sys

if sys.version_info <= (3, 5):
    import imp
else:
    import importlib.util


# --------------------------------------------------------------------------
# Command module class; wraps a single command-module.

class CommandModule(object):

    _log = logging.getLogger("module")

    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._name = os.path.basename(path).split('.')[0]
        self._loaded = False

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__,
                           os.path.basename(self._path))

    @property
    def loaded(self):
        return self._loaded

    def load(self):
        if self._loaded: return
        self._log.info("%s: Loading module: '%s'", self, self._path)

        # Attempt to load and execute the module; handle any exceptions.
        # Use *imp* for Python versions 3.5 and below; use *importlib.util*
        #  for versions 3.6 and above.
        try:
            name = self._name
            if sys.version_info <= (3, 5):
                import_dirs = [os.path.dirname(self._path)]
                file, pathname, description = imp.find_module(name,
                                                              import_dirs)
                with file:
                    imp.load_module(name, file, pathname, description)
            else:
                spec = importlib.util.spec_from_file_location(name,
                                                              self._path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
        except Exception as e:
            self._log.exception("%s: Error loading module: %s", self, e)
            self._loaded = False
            return

        self._loaded = True

    def unload(self):
        if not self._loaded: return
        self._log.info("%s: Unloading module: '%s'", self, self._path)

        # If the module has a top-level 'unload' function, call it.
        unload_func = getattr(sys.modules[self._name], 'unload', None)
        if unload_func:
            try:
                unload_func()
            except Exception as e:
                self._log.exception("%s: Error calling module function "
                                    " 'unload': %s", self, e)

        # Unload the module.
        del sys.modules[self._name]

        self._loaded = False

    def check_freshness(self):
        pass


# --------------------------------------------------------------------------
# Command module directory class.

class CommandModuleDirectory(object):

    _log = logging.getLogger("directory")

    def __init__(self, path, excludes=None, recursive=False):
        if excludes is None:
            excludes = []

        self._path = os.path.abspath(path)
        self._excludes = excludes
        self._recursive = recursive
        self._modules = {}

    def load(self):
        valid_paths = self._get_valid_paths()

        # Remove any deleted modules.
        for path, module_ in self._modules.items():
            if path not in valid_paths:
                del self._modules[path]
                module_.unload()

        # Add any new modules.
        for path in valid_paths:
            if path not in self._modules:
                if os.path.isfile(path):
                    module_ = CommandModule(path)
                elif os.path.isdir(path):
                    module_ = CommandModuleDirectory(path, self._excludes,
                                                     self._recursive)
                module_.load()
                self._modules[path] = module_
            else:
                module_ = self._modules[path]
                module_.check_freshness()

    @property
    def loaded(self):
        return not any([
            module_ for module_ in self._modules.values()
            if not module_.loaded
        ])

    def _get_valid_paths(self):
        self._log.info("Looking for command modules here: %s", self._path)
        valid_paths = []
        for filename in os.listdir(self._path):
            path = os.path.abspath(os.path.join(self._path, filename))
            if not (self._recursive or os.path.isfile(path)):
                continue
            if path in self._excludes:
                continue

            # Only apply _*.py to files, not directories.
            is_file = os.path.isfile(path)
            if is_file and not (os.path.basename(path).startswith("_") and
                                os.path.splitext(path)[1] == ".py"):
                continue
            valid_paths.append(path)
        self._log.info("Valid paths: %s", ", ".join(valid_paths))
        return valid_paths

    def unload(self):
        self._log.info("%s: Unloading directory: '%s'", self, self._path)
        for path, module_ in tuple(self._modules.items()):
            del self._modules[path]
            module_.unload()

    def check_freshness(self):
        pass

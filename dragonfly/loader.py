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

import os.path
import logging

# --------------------------------------------------------------------------
# Command module class; wraps a single command-module.


class CommandModule(object):

    _log = logging.getLogger("module")

    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._namespace = None
        self._loaded = False

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__,
                           os.path.basename(self._path))

    @property
    def loaded(self):
        return self._loaded

    def load(self):
        self._log.info("%s: Loading module: '%s'" % (self, self._path))

        # Prepare namespace in which to execute the
        namespace = {"__file__": self._path}

        # Attempt to execute the module; handle any exceptions.
        try:
            exec(compile(open(self._path).read(), self._path, 'exec'),
                 namespace)
        except Exception as e:
            self._log.exception("%s: Error loading module: %s" % (self, e))
            self._loaded = False
            return

        self._loaded = True
        self._namespace = namespace

    def unload(self):
        self._log.info("%s: Unloading module: '%s'" % (self, self._path))

    def check_freshness(self):
        pass


# --------------------------------------------------------------------------
# Command module directory class.

class CommandModuleDirectory(object):

    _log = logging.getLogger("directory")

    def __init__(self, path, excludes=None):
        self._path = os.path.abspath(path)
        self._excludes = excludes
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
                module_ = CommandModule(path)
                module_.load()
                self._modules[path] = module_
            else:
                module_ = self._modules[path]
                module_.check_freshness()

    def _get_valid_paths(self):
        self._log.info("Looking for command modules here: %s" % (self._path,))
        valid_paths = []
        for filename in os.listdir(self._path):
            path = os.path.abspath(os.path.join(self._path, filename))
            if not os.path.isfile(path):
                continue
            if not (os.path.basename(path).startswith("_") and
                    os.path.splitext(path)[1] == ".py"):
                continue
            if path in self._excludes:
                continue
            valid_paths.append(path)
        self._log.info("Valid paths: %s" % (", ".join(valid_paths),))
        return valid_paths

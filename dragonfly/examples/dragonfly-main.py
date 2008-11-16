#
# This file is a command-module for Dragonfly.
# (c) Copyright 2008 by Christo Butcher
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>
#

"""
Command-module loader for WSR
=============================

This script can be used to look Dragonfly command-modules 
for use with Window Speech Recognition.  It scans the 
directory it's in and loads any ``*.py`` it finds.

"""


import time
import os.path
import pythoncom

import dragonfly.log as log_
from dragonfly.engines.engine import get_sapi5_engine
engine = get_sapi5_engine()
engine.speak('begin!')


#---------------------------------------------------------------------------
# Command module class; wraps a single command-module.

class CommandModule(object):

    _log = log_.get_log("module")

    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._namespace = None
        self._loaded = False

    def __str__(self):
        return "%s(%r)" % (self.__class__.__name__,
                           os.path.basename(self._path))

    def load(self):
        self._log.error("%s: Loading module: %r" % (self, self._path))

        # Prepare namespace in which to execute the 
        namespace = {}
        namespace["__file__"] = self._path

        # Attempt to execute the module; handle any exceptions.
        try:
            execfile(self._path, namespace)
        except Exception, e:
            self._log.error("%s: Error loading module: %s" % (self, e))
            self._loaded = False
            return

        self._loaded = True
        self._namespace = namespace

    def unload(self):
        pass

    def check_freshness(self):
        pass


#---------------------------------------------------------------------------
# Command module directory class.

class CommandModuleDirectory(object):

    _log = log_.get_log("directory")

    def __init__(self, path, excludes=None):
        self._path = os.path.abspath(path)
        self._excludes = excludes
        self._modules = {}

    def load(self):
        valid_paths = self._get_valid_paths()

        # Remove any deleted modules.
        for path, module in self._modules.items():
            if path not in valid_paths:
                del self._modules[path]
                module.unload()

        # Add any new modules.
        for path in valid_paths:
            if path not in self._modules:
                module = CommandModule(path)
                module.load()
                self._modules[path] = module
            else:
                module = self._modules[path]
                module.check_freshness()

    def _get_valid_paths(self):
        valid_paths = []
        for filename in os.listdir(self._path):
            path = os.path.abspath(os.path.join(self._path, filename))
            if not os.path.isfile(path):
                continue
            if not os.path.splitext(path)[1] == ".py":
                continue
            if path in self._excludes:
                continue
            valid_paths.append(path)
        self._log.error("valid paths: %r" % valid_paths)
        return valid_paths


#---------------------------------------------------------------------------
# Main event driving loop.

path = os.path.dirname(__file__)
directory = CommandModuleDirectory(path, excludes=[__file__])
directory.load()

engine.speak('beginning loop!')
while 1:
#    engine.speak('loop!')
    pythoncom.PumpWaitingMessages()
    time.sleep(1)

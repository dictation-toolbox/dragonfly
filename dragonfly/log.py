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
Dragonfly's logging infrastructure is defined in the ``dragonfly.log``
module. It defines sane defaults for the various loggers used in the library
as well as functions for setting up logging and tracing.

Adjusting logger levels
----------------------------------------------------------------------------

Dragonfly's logger levels can be adjusted much like Python logger levels:

..  code::

    import logging
    logging.getLogger("engine").setLevel(logging.DEBUG)

The one caveat is that this must be done *after* the :meth:`setup_log`
function is called, otherwise the levels you set will be overridden.
By default, the function is only called near the top of the module loader
scripts (e.g. *dragonfly/examples/dfly-loader-wsr.py*), not within dragonfly
itself.

It is not necessary to call :meth:`setup_log` at all. Standard Python
logging functions such as :meth:`basicConfig` can be used at the top of
module loader scripts instead.

If you are not using dragonfly with a module loader, you will need to set up
a logging handler to avoid messages like tho following::

    No handlers could be found for logger "typeables"


Functions
----------------------------------------------------------------------------

"""

import sys
import os.path
import logging


# --------------------------------------------------------------------------
# Sane defaults for logger names and associated levels.

_debug     = logging.DEBUG
_info      = logging.INFO
_warning   = logging.WARNING
_error     = logging.ERROR
_critical  = logging.CRITICAL
default_levels = {
                  "":                     (_warning, _warning),
                  "engine":               (_info, _info),
                  "engine.compiler":      (_warning, _info),
                  "engine.timer":         (_warning, _info),
                  "grammar":              (_warning, _critical),
                  "grammar.load":         (_warning, _info),
                  "grammar.begin":        (_info, _info),
                  "grammar.results":      (_warning, _warning),
                  "grammar.decode":       (_warning, _info),
                  "grammar.eval":         (_warning, _warning),
                  "grammar.process":      (_warning, _warning),
                  "lang":                 (_warning, _info),
                  "compound.parse":       (_warning, _info),
                  "dictation.formatter":  (_warning, _warning),
                  "dictation.word_parser":  (_warning, _warning),
                  "dictation.word_parser_factory":  (_warning, _warning),
                  "action":               (_warning, _warning),
                  "action.init":          (_warning, _warning),
                  "action.exec":          (_warning, _warning),
                  "context":              (_warning, _info),
                  "context.match":        (_warning, _info),
                  "rpc.server":           (_warning, _info),
                  "rpc.methods":          (_warning, _info),
                  "werkzeug":             (_warning, _warning),
                  "jsonrpc.manager":      (_critical, _critical),
                  "rule":                 (_warning, _info),
                  "clipboard":            (_warning, _info),
                  "config":               (_warning, _info),
                  "module":               (_info, _info),
                  "monitor.init":         (_warning, _info),
                  "dfly.test":            (_debug, _debug),
                  "accessibility":        (_info, _info),
                  "keyboard":             (_warning, _warning),
                  "typeables":            (_warning, _warning),
                 }


# --------------------------------------------------------------------------
# Logging filter class which filters out messages of a given name below
#  a given level.

class NameLevelFilter(logging.Filter):
    """"""
    def __init__(self, name, level):
        self.name = name
        self.level = level
        super(NameLevelFilter, self).__init__(name)

    def filter(self, record):
        if record.name == self.name:
            if record.levelno >= self.level:
                return True
            else:
                return False
        else:
            return True


# --------------------------------------------------------------------------

class DispatchingHandler(logging.Handler):
    """"""

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.handler_filter_pairs = []

    def filter(self, record):
        return True

    def add_handler_filter_pair(self, handler, filter):
        self.handler_filter_pairs.append((handler, filter))

    def emit(self, record):
        # print "dispatching", self, self.handler_filter_pairs, record
        # import traceback; print traceback.extract_stack()
        # import traceback; traceback.print_stack()
        for handler, filter in self.handler_filter_pairs:
            if filter.filter(record):
                handler.handle(record)


# --------------------------------------------------------------------------

def _setup_stderr_handler():
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(name)s (%(levelname)s): %(message)s")
    stderr_handler.setFormatter(formatter)
    return stderr_handler

_file_handler = None


def _setup_file_handler():
    global _file_handler
#    import traceback; traceback.print_stack()
    if not _file_handler:
        # Use ~/.dragonfly.log as the file for Dragonfly's log messages.
        home_path = os.path.expanduser("~")
        log_file_path = os.path.join(home_path, ".dragonfly.log")
        _file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter("%(asctime)s %(name)s (%(levelname)s):"
                                      " %(message)s")
        _file_handler.setFormatter(formatter)
    return _file_handler


# --------------------------------------------------------------------------

_stderr_handler = None
_dispatching_handlers = {}
_stderr_filters = {}
_file_filters = {}


def setup_log(use_stderr=True, use_file=True, use_stdout=False):
    """
    Setup Dragonfly's logging infrastructure with sane defaults.

    :param use_stderr: whether to output log messages to stderr
      (default: True).
    :param use_file: whether to output log messages to the
      *~/.dragonfly.log* log file (default: True).
    :param use_stdout: this parameter does nothing andhas been left in for
      backwards-compatibility (default: False).
    :type use_stderr: bool
    :type use_file: bool
    :type use_stdout: bool

    """
    global _dispatching_handlers
    global _stderr_handler, _file_handler
    global _stderr_filters, _file_filters

    # Remove any previously created dispatching handlers.
    for name, handler in _dispatching_handlers.items():
        logger = logging.getLogger(name)
        logger.removeHandler(handler)

    # Setup default handlers.
    if use_stderr:
        _stderr_handler = _setup_stderr_handler()
    if use_file:
        _file_handler = _setup_file_handler()

    # Create and register default filters.
    for name, levels in default_levels.items():
        stderr_level, file_level = levels
        handler = DispatchingHandler()
        _dispatching_handlers[name] = handler
        if use_stderr:
            stderr_filter = NameLevelFilter(name, stderr_level)
            handler.add_handler_filter_pair(_stderr_handler, stderr_filter)
            _stderr_filters[name] = stderr_filter
        if use_file:
            file_filter = NameLevelFilter(name, file_level)
            handler.add_handler_filter_pair(_file_handler, file_filter)
            _file_filters[name] = file_filter
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(min(stderr_level, file_level))
        logger.propagate = False


# --------------------------------------------------------------------------
# Function for setting up call tracing for low-level debugging.

def setup_tracing(output, limit=None):
    """
    Setup call tracing for low-level debugging.

    :param output: the file to write tracing messages to.
    :type output: file
    :param limit: the recursive depth limit for tracing (default: None).
    :type limit: int|None
    """
    from pkg_resources import resource_filename
    library_prefix = os.path.dirname(resource_filename(__name__, "setup.py"))
    print("prefix:", library_prefix)
    exclude_filenames = ("parser.py",)

    def _tracing_callback(frame, event, arg):
        # Retrieve current function name, line number, etc.
        code_object = frame.f_code
        function_name = code_object.co_name
        line_number = frame.f_lineno
        filename = code_object.co_filename
        if not filename.startswith(library_prefix):
            return
        else:
            filename = filename[len(library_prefix)+1:]
        if os.path.basename(filename) in exclude_filenames:
            return

        depth = 0
        if limit is not None:
            # Determine call depth of current frame.
            parent_frame = frame
            while parent_frame:
                parent_frame = parent_frame.f_back
                depth += 1
            del parent_frame
            if depth > limit:
                return

        # Write message to output.
        indented_function_name = ("  " * depth) + function_name
        output.write("%2d %-40s %5s %-40s\n" % (depth, indented_function_name,
                                                line_number, filename))
        output.flush()

    sys.settrace(_tracing_callback)

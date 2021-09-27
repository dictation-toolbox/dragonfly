#
# This file is part of Dragonfly.
# (c) Copyright 2018 by Dane Finlay
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

import argparse
import ast
import glob
import logging
import os
import re
import sys
import time

import six

from dragonfly import get_engine, MimicFailure, EngineError
from dragonfly.loader import CommandModule, CommandModuleDirectory

LOG = logging.getLogger("command")


#---------------------------------------------------------------------------
# CLI helper functions.

def _set_logging_level(args):
    if args.quiet:
        args.log_level = "WARNING"

    # Set up logging with the specified logging level.
    logging.basicConfig(level=getattr(logging, args.log_level))


def _init_engine(args):
    # Retrieve the engine option pairs from the arguments.
    # TODO Remove multiple engine options per -o arg in version 1.0.0.
    options = {}
    for argument in args.engine_options:
        for options_list in argument:
            for option, value in options_list:
                options[option] = value

    try:
        # Initialize the specified engine with options, catching and
        #  reporting errors.
        engine = get_engine(args.engine, **options)
    except EngineError as e:
        LOG.error(e)
        engine = None

    # Set the engine language if necessary.
    if engine and args.language != engine.language:
        try:
            engine.language = args.language
        except AttributeError:
            LOG.error("Cannot set language for engine %r", engine.name)
            engine = None

    return engine


def _load_cmd_modules(args):
    # Retrieve filenames from the arguments.
    files = []
    for lst in args.files:
        files.extend(lst)

    # Load each specified command module.  Errors during loading will be
    #  caught and logged.
    return_code = 0
    for f in files:
        module_ = CommandModule(f)
        module_.load()
        if not module_.loaded:
            return_code = 1

    # Return the overall success of module loading.
    return return_code


def _load_cmd_module_dirs(args):
    # Load command modules from each specified directory.  Errors during
    #  loading will be caught and logged.
    recursive = args.recursive
    return_code = 0
    for d in args.module_dirs:
        module_directory = CommandModuleDirectory(d, recursive=recursive)
        module_directory.load()
        if not module_directory.loaded:
            return_code = 1

    # Return the overall success of module loading.
    return return_code


def _on_begin():
    print("Speech start detected.")


def _on_recognition(words):
    message = u"Recognized: %s" % u" ".join(words)

    # This only seems to be an issue with Python 2.7 on Windows.
    if six.PY2:
        encoding = sys.stdout.encoding or "ascii"
        message = message.encode(encoding, errors='replace')
    print(message)


def _on_failure():
    print("Sorry, what was that?")


def _do_recognition(engine, args):
    # Start the engine's main recognition loop, registering recognition
    # callback functions only if necessary.
    try:
        if not args.no_recobs_messages:
            engine.do_recognition(_on_begin, _on_recognition, _on_failure)
        else:
            engine.do_recognition()
    except KeyboardInterrupt:
        pass


#---------------------------------------------------------------------------
# Main CLI functions.

def cli_cmd_test(args):
    # Set the logging level.
    _set_logging_level(args)

    # Initialise the specified engine. Return early if there was an error.
    engine = _init_engine(args)
    if engine is None:
        return 1

    # Connect to the engine, load command modules, take input from stdin and
    # disconnect from the engine if interrupted or if EOF is received.
    LOG.debug("Testing with engine '%s'", args.engine)
    with engine.connection():
        # Load each command module. Errors during loading will be caught and
        # logged. Use the overall success of module loading and/or mimic
        # calls as the return code.
        return_code = _load_cmd_modules(args)

        # Return early if --no-input was specified.
        if args.no_input:
            return return_code

        # Get the number of seconds to delay between each mimic() call
        # (default 0). Log a message if the delay is non-zero.
        delay = args.delay
        if delay:
            LOG.info("Calls to mimic() will be delayed by %.2f seconds "
                     "as specified", delay)

        # Read lines from stdin and pass them to engine.mimic. Strip excess
        # white space from each line. Report any mimic failures.
        LOG.info("Enter commands to mimic followed by new lines.")
        try:
            # Use iter to avoid a bug in Python 2.x:
            # https://bugs.python.org/issue3907
            for line in iter(sys.stdin.readline, ''):
                line = line.strip()
                if not line:  # skip empty lines.
                    continue

                # Delay between mimic() calls if necessary.
                if delay > 0:
                    time.sleep(delay)

                try:
                    engine.mimic(line.split())
                    LOG.info("Mimic success for words: %s", line)
                except MimicFailure:
                    LOG.error("Mimic failure for words: %s", line)
                    return_code = 1
        except KeyboardInterrupt:
            pass

    # Return the success of this command.
    return return_code


def cli_cmd_load(args):
    # Set the logging level.
    _set_logging_level(args)

    # Initialise the specified engine. Return early if there was an error.
    engine = _init_engine(args)
    if engine is None:
        return 1

    # Connect the engine, load each command module and start the main
    # recognition loop. The loop will normally exit on engine.disconnect()
    # or a keyboard interrupt.
    LOG.debug("Recognizing with engine '%s'", args.engine)
    with engine.connection():
        return_code = _load_cmd_modules(args)

        # Return early if --no-input was specified.
        if args.no_input:
            return return_code

        _do_recognition(engine, args)

    # Return the success of module loading.
    return return_code


def cli_cmd_load_directory(args):
    # Set the logging level.
    _set_logging_level(args)

    # Initialise the specified engine. Return early if there was an error.
    engine = _init_engine(args)
    if engine is None:
        return 1

    # Connect the engine, load each command module and start the main
    # recognition loop. The loop will normally exit on engine.disconnect()
    # or a keyboard interrupt.
    LOG.debug("Recognizing with engine '%s'", args.engine)
    with engine.connection():
        if args.recursive:
            LOG.info("Loading command modules in sub-directories as "
                     "specified (recursive mode).")
        return_code = _load_cmd_module_dirs(args)

        # Return early if --no-input was specified.
        if args.no_input:
            return return_code

        _do_recognition(engine, args)

    # Return the success of module loading.
    return return_code


_COMMAND_MAP = {
    "test": cli_cmd_test,
    "load": cli_cmd_load,
    "load-directory": cli_cmd_load_directory,
}


#---------------------------------------------------------------------------
# argparse helper functions.

def _build_argument(*args, **kwargs):
    return args, kwargs


def _add_arguments(parser, *arguments):
    for (args, kwargs) in arguments:
        parser.add_argument(*args, **kwargs)


def _smart_cast(value):
    """ Attempts to convert given str to a more precise type based on Python literals. """
    try:
        return ast.literal_eval(value)
    except:
        return value


def _engine_options_string(string):
    if '=' not in string:
        msg = "Invalid engine option: %r" % string
        raise argparse.ArgumentTypeError(msg)

    # Return a list of key/value arguments separated by commas or spaces.
    # TODO Remove multiple engine options per -o arg in version 1.0.0.
    options = []
    for sub_string in re.split('[,\\s]', string):
        if not sub_string:  # Filter out empty strings.
            continue

        # There must be one valid engine option per sub-string.
        parts = sub_string.split('=')
        if len(parts) != 2 or not (parts[0] and parts[1]):
            msg = "Invalid engine option: %r" % sub_string
            raise argparse.ArgumentTypeError(msg)

        arg = parts[0]
        value = _smart_cast(parts[1])
        options.append((arg, value))

    return options


def _filename(string):
    """ Same as argparse.FileType, but returns the filename. """
    f = argparse.FileType("r")(string)
    fname = f.name
    f.close()
    return fname


def _valid_filename_or_pattern(string):
    # Expand glob patterns or interpret the string as an existing file path.
    if "?" in string or "*" in string:
        files = glob.glob(string)
        if files:
            result = [_filename(f) for f in files]
        else:
            result = [_filename(string)]
    else:
        result = [_filename(string)]
    return result


def _valid_directory_path(string):
    if not os.path.isdir(string):
        msg = "No such directory: %r" % string
        raise argparse.ArgumentTypeError(msg)
    return string


#---------------------------------------------------------------------------
# Main argparse functions.

def make_arg_parser():
    # pylint: disable=too-many-locals
    # Suppress warnings about too many local variables in this function.

    parser = argparse.ArgumentParser(
        prog="python -m dragonfly",
        description="Command-line interface to the Dragonfly speech "
                    "recognition framework"
    )
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    # Define common arguments.
    cmd_module_files_argument = _build_argument(
        "files", metavar="file", nargs="*", type=_valid_filename_or_pattern,
        help="Command module file(s)."
    )

    # TODO Rename to "--engine-option" in version 1.0.0.
    engine_options_argument = _build_argument(
        "-o", "--engine-options", default=[], nargs="+", action="append",
        type=_engine_options_string,
        help="One or more engine options to be passed to *get_engine()*. "
             "Each option should specify a key word argument and value. "
             "Multiple options should be separated by spaces or commas. "
             "Values are treated as Python literals if possible, "
             "otherwise as strings."
    )

    language_argument = _build_argument(
        "--language", default="en",
        help="Speaker language to use. Only applies if using an engine "
        "backend that supports changing the language (e.g. the \"text\" "
        "engine)."
    )
    no_input_argument = _build_argument(
        "-n", "--no-input", default=False, action="store_true",
        help="Whether to load command modules and then exit without "
             "reading input from stdin or recognizing speech."
    )
    log_level_argument = _build_argument(
        "-l", "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level to use."
    )
    quiet_argument = _build_argument(
        "-q", "--quiet", default=False, action="store_true",
        help="Equivalent to '-l WARNING' -- suppresses INFO and DEBUG "
             "logging."
    )

    # Create the parser for the "test" command.
    parser_test = subparsers.add_parser(
        "test",
        help="Load grammars from Python files for testing with a "
        "dragonfly engine. By default input from stdin is passed to "
        "engine.mimic() after command modules are loaded."
    )
    engine_argument = _build_argument(
        "-e", "--engine", default="text",
        help="Name of the engine to use for testing."
    )
    delay_argument = _build_argument(
        "-d", "--delay", default=0, type=float,
        help="Time in seconds to delay before mimicking each command. This "
        "is useful for testing contexts."
    )
    _add_arguments(
        parser_test,
        cmd_module_files_argument, engine_argument, engine_options_argument,
        language_argument, no_input_argument, delay_argument,
        log_level_argument, quiet_argument
    )

    # Define common arguments for the "load" and "load-directory" commands.
    engine_argument = _build_argument(
        "-e", "--engine", default=None,
        help="Name of the engine to use for loading and recognizing from "
             "command modules. By default, this is the first available "
             "engine backend."
    )
    no_recobs_messages_argument = _build_argument(
        "--no-recobs-messages", default=False, action="store_true",
        help="Disable recognition state messages for each spoken phrase."
    )

    # Create the parser for the "load" command.
    parser_load = subparsers.add_parser(
        "load", help="Load and recognize from command module files."
    )
    _add_arguments(
        parser_load,
        cmd_module_files_argument, engine_argument, engine_options_argument,
        language_argument, no_input_argument, no_recobs_messages_argument,
        log_level_argument, quiet_argument
    )

    # Create the parser for the "load-directory" command.
    parser_load_directory = subparsers.add_parser(
        "load-directory",
        help="Load and recognize from command module files in one or more"
             " directories.  Only module files starting with an underscore"
             " (_*.py) are loaded by this command."
    )
    module_dirs_argument = _build_argument(
        "module_dirs", metavar="dir", nargs="+", type=_valid_directory_path,
        help="One or more command module directories."
    )
    recursive_argument =  _build_argument(
        "-r", "--recursive", default=False, action="store_true",
        help="Whether to recursively load command modules in "
             "sub-directories."
    )
    _add_arguments(
        parser_load_directory,
        module_dirs_argument, recursive_argument, engine_argument,
        engine_options_argument, language_argument, no_input_argument,
        no_recobs_messages_argument, log_level_argument, quiet_argument
    )

    # Return the argument parser.
    return parser


def main():
    # Parse the arguments and get the relevant function. Exit if the command
    # is not implemented.
    args = make_arg_parser().parse_args()

    def not_implemented(_):
        print("Command '%s' is not implemented" % args.command)
        return 1

    func = _COMMAND_MAP.get(args.command, not_implemented)

    # Call the function and exit using the result.
    return_code = func(args)
    exit(return_code)


if __name__ == '__main__':
    main()

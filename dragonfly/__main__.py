import argparse
import logging
import sys


from dragonfly import get_engine, MimicFailure
from dragonfly.engines.base.engine import EngineContext
from dragonfly.loader import CommandModule

logging.basicConfig()
_log = logging.getLogger("command")


def test_with_engine(args):
    # Initialise the specified engine, catching and reporting errors.
    try:
        engine = get_engine(args.engine)
        _log.debug("Testing with engine '%s'" % args.engine)
    except Exception as e:
        _log.error(e)
        return 1

    # Set the logging level of the root logger.
    if args.quiet:
        args.log_level = "WARNING"
    logging.root.setLevel(getattr(logging, args.log_level))

    # Connect to the engine, load grammar modules, take input from stdin and
    # disconnect from the engine if interrupted or if EOF is received.
    with engine.connection():
        # Load each module. Errors during loading will be caught and logged.
        # Use the overall success of module loading and/or mimic calls as
        # the return code.
        return_code = 0
        for f in args.files:
            module_ = CommandModule(f.name)
            module_.load()

            if not module_.loaded:
                return_code = 1

            # Also close each file object created by argparse.
            f.close()

        # Read lines from stdin and pass them to engine.mimic. Strip excess
        # white space from each line. Report any mimic failures.
        if args.no_input:
            # Return early if --no-input was specified.
            return return_code
        _log.info("Enter commands to mimic followed by new lines.")
        try:
            # Use iter to avoid a bug in Python 2.x:
            # https://bugs.python.org/issue3907
            for line in iter(sys.stdin.readline, ''):
                line = line.strip()
                if not line:  # skip empty lines.
                    continue

                try:
                    engine.mimic(line.split())
                    _log.info("Mimic success for words: %s" % line)
                except MimicFailure:
                    _log.error("Mimic failure for words: %s" % line)
                    return_code = 1
        except KeyboardInterrupt:
            pass

    return return_code


_command_map = {
    "test": test_with_engine
}


def make_arg_parser():
    parser = argparse.ArgumentParser(
        prog="python -m dragonfly",
        description="Command-line interface to the Dragonfly speech "
                    "recognition framework"
    )
    subparsers = parser.add_subparsers(dest='subparser_name')

    # Create the parser for the "test" command.
    parser_test = subparsers.add_parser(
        "test",
        help="Load grammars from Python files for testing with a "
        "dragonfly engine. By default input from stdin is passed to "
        "engine.mimic() after command modules are loaded."
    )
    parser_test.add_argument(
        "files", metavar="file", nargs="+", type=argparse.FileType("r"),
        help="Command module file(s)."
    )
    parser_test.add_argument(
        "-e", "--engine", default="text",
        help="Name of the engine to use for testing."
    )
    parser_test.add_argument(
        "-l", "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level to use."
    )
    parser_test.add_argument(
        "-n", "--no-input", default=False, action="store_true",
        help="Whether to load command modules and then exit without "
             "reading input from stdin."
    )
    parser_test.add_argument(
        "-q", "--quiet", default=False, action="store_true",
        help="Equivalent to '-l WARNING' -- suppresses INFO and DEBUG "
             "logging."
    )
    return parser


def main():
    # Parse the arguments and get the relevant function. Exit if the command
    # is not implemented.
    args = make_arg_parser().parse_args()

    def not_implemented(_):
        print("Command '%s' is not implemented" % args.subparser_name)
        return 1

    func = _command_map.get(args.subparser_name, not_implemented)

    # Call the function and exit using the result.
    return_code = func(args)
    exit(return_code)


if __name__ == '__main__':
    main()

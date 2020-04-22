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
Test cases for the logging framework
============================================================================

"""

import sys
import logging
import logging.handlers
import unittest
import dragonfly.log as log


#===========================================================================

class OutputCapturer(object):

    def __init__(self):
        self.blocks = []

    def write(self, data):
        self.blocks.append(data)

    def flush(self):
        pass

    def clear(self):
        self.blocks = []

    @property
    def lines(self, prefix=""):
        if not self.blocks:
            return ()
        else:
            text = "".join(self.blocks).splitlines()
            text = prefix + ("\n" + prefix).join(text)
            return text.splitlines()


#---------------------------------------------------------------------------

class LogTestCase(unittest.TestCase):
    """ Test behavior of logging system. """

    def setUp(self):
        self._original_stdout = sys.stdout
        self._output = OutputCapturer()
        sys.stdout = self._output
        self._original_stderr = sys.stderr
        self._error = OutputCapturer()
        sys.stderr = self._error

    def tearDown(self):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
#        if self._output.blocks:
#            prefix = "Output:  "
#            output = "".join(self._output.blocks).splitlines()
#            output = prefix + ("\n" + prefix).join(output)
#            print output
#        if self._error.blocks:
#            prefix = "Error:   "
#            text = "".join(self._error.blocks).splitlines()
#            text = prefix + ("\n" + prefix).join(text)
#            print text
        self._output = None
        self._error = None

    def test_filtering(self):
        """ Verify that log messages are filtered according to level. """
        log.setup_log()
        logger = logging.getLogger("grammar")
        logger.debug("test_filtering - debug")
        logger.info("test_filtering - info")
        logger.warning("test_filtering - warning")
        logger.error("test_filtering - error")
        expected = ["grammar (WARNING): test_filtering - warning",
                    "grammar (ERROR): test_filtering - error"]
        self.assertEqual(self._error.lines, expected)

        self._error.clear()
        logger = logging.getLogger("grammar.begin")
        logger.debug("test_filtering - debug")
        logger.info("test_filtering - info")
        logger.warning("test_filtering - warning")
        logger.error("test_filtering - error")
        expected = ["grammar.begin (INFO): test_filtering - info",
                    "grammar.begin (WARNING): test_filtering - warning",
                    "grammar.begin (ERROR): test_filtering - error"]
        self.assertEqual(self._error.lines, expected)

        self._error.clear()
        logger = logging.getLogger("grammar.load")
        logger.debug("test_filtering - debug")
        logger.info("test_filtering - info")
        logger.warning("test_filtering - warning")
        logger.error("test_filtering - error")
        expected = ["grammar.load (WARNING): test_filtering - warning",
                    "grammar.load (ERROR): test_filtering - error"]
        self.assertEqual(self._error.lines, expected)

    def _new_lines(self):
        filename = None
        if not hasattr(self, "_previous_line_count"):
            self._previous_line_count = 0
        lines = open(filename).readlines()
        new_lines = lines[self._previous_line_count:]
        self._previous_line_count = len(lines)
        return new_lines


#===========================================================================

if __name__ == "__main__":
    unittest.main()

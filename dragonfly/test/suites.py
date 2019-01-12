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

import doctest
import os.path
import sys
import unittest

from six import PY3

from dragonfly.test.engine_suite import EngineTestSuite


# ==========================================================================

common_names = [
    "test_accessibility",
    "test_contexts",
    "test_engine_nonexistent",
    "test_language_de_number",
    "test_language_en_number",
    "test_language_nl_number",
    "test_log",
    "test_parser",
    "test_timer",
    "doc:documentation/test_action_base_doctest.txt",
    "doc:documentation/test_grammar_elements_basic_doctest.txt",
    "doc:documentation/test_grammar_elements_compound_doctest.txt",
    "doc:documentation/test_grammar_list_doctest.txt",
    "doc:documentation/test_recobs_doctest.txt",
]

# Only include common Windows-only tests on Windows.
if sys.platform == "nt":
    common_names.extend([
        "test_window",
        "test_actions",
    ])

natlink_names = [
    "test_dictation",
    "test_engine_natlink",
    # "doc:documentation/test_word_formatting_v10_doctest.txt",
    "doc:documentation/test_word_formatting_v11_doctest.txt",
]

sapi5_names = [
    "test_dictation",
    "test_engine_sapi5",
]

sphinx_names = [
    "test_engine_sphinx",
]

text_names = [
    "test_engine_text",
    "test_engine_text_dictation",
]

# ==========================================================================

def build_suite(suite, names):
    # Load test cases from specified names.
    loader = unittest.defaultTestLoader
    for name in names:
        if name.startswith("test_"):
            suite.addTests(loader.loadTestsFromName(name))
        elif name.startswith("doc:"):
            # Skip doc tests for Python 3.x because of incompatible Unicode
            # string comparisons in some tests.
            # TODO Use pytest instead for its ALLOW_UNICODE doctest flag.
            if PY3:
                continue

            # Load doc tests using a relative path.
            path = os.path.join("..", "..", "%s" % name[4:])
            suite.addTests(doctest.DocFileSuite(path))
        else:
            raise Exception("Invalid test name: %r." % (name,))
    return suite


natlink_suite  = build_suite(EngineTestSuite("natlink"),
                             natlink_names + common_names)
sapi5_suite    = build_suite(EngineTestSuite("sapi5"),
                             sapi5_names + common_names)
sphinx_suite   = build_suite(EngineTestSuite("sphinx"),
                             sphinx_names + common_names)
text_suite     = build_suite(EngineTestSuite("text"),
                             text_names + common_names)


if __name__ == "__main__":
    # TODO Have a way of running all test suites
    runner = unittest.TextTestRunner()
    runner.run(text_suite)

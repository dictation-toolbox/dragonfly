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
import logging
import os
import os.path
import unittest

from six import PY3

from dragonfly.log import setup_log
from dragonfly.test.engine_suite import EngineTestSuite

# Setup logging.
_log = logging.getLogger("dfly.test")
setup_log()


# ==========================================================================

common_names = [
    "test_accessibility",
    "test_actions",
    # "test_contexts",  # disabled for now
    "test_engine_nonexistent",
    "test_log",
    "test_parser",
    "test_rpc",
    "test_timer",
    "test_window",
    "doc:documentation/test_action_base_doctest.txt",
    "doc:documentation/test_grammar_elements_basic_doctest.txt",
    "doc:documentation/test_grammar_elements_compound_doctest.txt",
    "doc:documentation/test_grammar_list_doctest.txt",
    "doc:documentation/test_recobs_doctest.txt",
]

# Define spoken language test files. All of them work with the natlink and
# text engines. The English tests should work with sapi5 and sphinx by
# default.
language_names = [
    "test_language_de_number",
    "test_language_en_number",
    "test_language_nl_number",
]


# Define the tests to run for DNS versions 10 and below.
natlink_10_names = [
    "test_dictation",
    "test_engine_natlink",
    "doc:documentation/test_word_formatting_v10_doctest.txt",
] + common_names + language_names

# Define the tests to run for DNS versions 11 and above.
natlink_11_names = [
    "test_dictation",
    "test_engine_natlink",
    "doc:documentation/test_word_formatting_v11_doctest.txt",
] + common_names + language_names

sapi5_names = [
    "test_engine_sapi5",
    "test_language_en_number",
] + common_names

# Don't include recognition observer tests for sapi5 because its quirky
# behaviour requires separate tests. These are in test_engine_sapi5.
sapi5_names.remove("doc:documentation/test_recobs_doctest.txt")

sphinx_names = [
    "test_engine_sphinx",
    "test_language_en_number",
] + common_names

kaldi_names = [
    "test_engine_kaldi",
    # "test_language_en_number",
] + common_names
kaldi_names.remove("doc:documentation/test_grammar_list_doctest.txt")
kaldi_names.remove("doc:documentation/test_recobs_doctest.txt")

text_names = [
    "test_contexts",
    "test_engine_text",
    "test_engine_text_dictation",
] + common_names + language_names

# ==========================================================================

def build_suite(suite, names):
    # Load test cases from specified names.
    loader = unittest.defaultTestLoader
    for name in names:
        if name.startswith("test_"):
            # Use full module names so the loader can import the files
            # correctly.
            name = "dragonfly.test." + name
            suite.addTests(loader.loadTestsFromName(name))
        elif name.startswith("doc:"):
            # Skip doc tests for Python 3.x because of incompatible Unicode
            # string comparisons in some tests.
            # TODO Use pytest instead for its ALLOW_UNICODE doctest flag.
            if PY3:
                continue

            # Load doc tests using a relative path.
            path = os.path.join("..", "..", name[4:])
            suite.addTests(doctest.DocFileSuite(path))
        else:
            raise Exception("Invalid test name: %r." % (name,))
    return suite


sapi5_suite       = build_suite(EngineTestSuite("sapi5"), sapi5_names)
sapi5inproc_suite = build_suite(EngineTestSuite("sapi5inproc"), sapi5_names)
sphinx_suite      = build_suite(EngineTestSuite("sphinx"), sphinx_names)
kaldi_suite       = build_suite(EngineTestSuite("kaldi"), kaldi_names)
text_suite        = build_suite(EngineTestSuite("text"), text_names)


# Build the natlink test suite for the current version of DNS.
try:
    import natlinkstatus
    dns_version = int(natlinkstatus.NatlinkStatus().getDNSVersion())
except:
    # Couldn't get the DNS version for whatever reason.
    dns_version = None


# Use different test names depending on the DNS version. Fallback on v11 if
# the version is unknown.
if dns_version and dns_version <= 10:
    natlink_names = natlink_10_names
else:
    natlink_names = natlink_11_names


# Exclude the grammar lists doctest file for DNS 15 and above due to a minor
# bug with natlink/Dragon.
if dns_version and dns_version >= 15:
    lists_doctest = "doc:documentation/test_grammar_list_doctest.txt"
    natlink_names.remove(lists_doctest)
    _log.warning("DNS version %d detected! Excluding test file: %s"
                 % (dns_version, lists_doctest[4:]))
    _log.warning("List functionality doesn't work if used in modules not "
                 "loaded by natlinkmain.")
    _log.warning("Please see: https://github.com/dictation-toolbox/dragonfly/pull/55")

natlink_suite    = build_suite(EngineTestSuite("natlink"), natlink_names)

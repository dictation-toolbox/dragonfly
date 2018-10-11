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

import unittest
import doctest
import pkg_resources
import os.path
from dragonfly.test.engine_suite import EngineTestSuite


#===========================================================================

common_names   = [
                  ".test_log",
                  ".test_actions",
                  ".test_parser",
#                  ".test_engine",
                  ".test_engine_nonexistent",
                  ".test_window",
                  ".test_timer",
                  ".test_dictation",
                  ".test_language_en_number",
                  ".test_language_de_number",
                  ".test_language_nl_number",
                  "doc:documentation/test_action_base_doctest.txt",
                  "doc:documentation/test_grammar_elements_basic_doctest.txt",
                  "doc:documentation/test_grammar_elements_compound_doctest.txt",
                  "doc:documentation/test_grammar_list_doctest.txt",
                 ]

natlink_names  = [
                  ".test_engine_natlink",
                  "doc:documentation/test_recobs_doctest.txt",
#                  "doc:documentation/test_word_formatting_v10_doctest.txt",
                  "doc:documentation/test_word_formatting_v11_doctest.txt",
                 ]

sapi5_names    = [
                  ".test_engine_sapi5",
                 ]

sphinx_names   = [
                  ".test_engine_sphinx",
                 ]
#===========================================================================

def build_suite(suite, names):
    # Determine the root directory of the source code files.  This is
    #  used for finding doctest files specified relative to that root.
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    project_root = os.path.abspath(project_root)

    # Load test cases from specified names.
    loader = unittest.defaultTestLoader
    for name in names:
        if name.startswith("."):
            name = "dragonfly.test" + name
            suite.addTests(loader.loadTestsFromName(name))
        elif name.startswith("doc:"):
            path = name[4:]
            path = os.path.join(project_root, *path.split("/"))
            path = os.path.abspath(path)
            suite.addTests(doctest.DocFileSuite(path))
        else:
            raise Exception("Invalid test name: %r." % (name,))
    return suite


natlink_suite  = build_suite(EngineTestSuite("natlink"),
                             natlink_names + common_names)
sapi5_suite    = build_suite(EngineTestSuite("sapi5"),
                             sapi5_names + common_names)
sphinx_suite    = build_suite(EngineTestSuite("sphinx"),
                             sphinx_names + common_names)

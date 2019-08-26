#
# This file  Is part of Dragonfly.
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
Loader of language-dependent objects
============================================================================

This file implements the loader for language-dependent objects within
the dragonfly.language sub-package.  At runtime it attempts to figure
out what the current user's language is, and then loads the appropriate
objects.

Examples of language-dependent objects within Dragonfly are the Integer,
Digits, and Number classes.

"""

import sys
import logging
from ..grammar.rule_base       import Rule
from ..grammar.elements_basic  import RuleRef
from ..error                   import DragonflyError


#---------------------------------------------------------------------------
# Loader class for accessing language-specific object at runtime.

class LanguageSpecificLoader(object):

    _log = logging.getLogger("lang")


    #-----------------------------------------------------------------------
    # Mapping of language tags to module names.  Each of the module names
    #  should implement the appropriate classes for the given
    #  speaker language.

    language_map = {
                    "ar":  "dragonfly.language.ar",
                    "de":  "dragonfly.language.de",
                    "en":  "dragonfly.language.en",
                    "id":  "dragonfly.language.id",
                    "ms":  "dragonfly.language.ms",
                    "nl":  "dragonfly.language.nl",
                   }


    def __init__(self, language=None):
        self._language = language
        self._module = None

    def __getattr__(self, name):
        return self.get_attribute(name)

    def get_attribute(self, name):
        # Make sure the appropriate language-specific module has been
        #  loaded and is available.
        if not self._module:
            self._load_module()

        # Attempt to retrieve the requested attribute from the
        #  language-specific module.
        try:
            return getattr(self._module, name)
        except AttributeError:
            # Raise an error unless getting ShortIntegerContent.
            if name != "ShortIntegerContent":
                raise DragonflyError("Language %r does not implement %r."
                                     % (self._language, name))
            else:
                self._log.warning("Language %r does not implement %r, "
                                  "falling back on %r."
                                  %(self._language, name, "IntegerContent"))
                return getattr(self._module, "IntegerContent")

    def _load_module(self):
        if not self._language:
            self._language = self._get_engine_language()
        self._module = self._load_module_for_language(self._language)

    def _get_engine_language(self):
        try:
            from ..engines import get_engine
            language = get_engine().language
        except Exception as e:
            self._log.exception("Failed to retrieve speaker language: %s" % e)
            raise
        return language

    def _load_module_for_language(self, language):
        # Lookup the module name for the given language.
        try:
            module_name = self.language_map[language]
        except KeyError:
            raise DragonflyError("Attempt to load unknown language: %r"
                                 % language)

        # Attempt to import the language-dependent module.
        try:
            top_module = __import__(module_name)
        except ImportError as e:
            self._log.exception("Failed to load module %r for language %r"
                                % (module_name, language))
            raise
        try:
            module = sys.modules[module_name]
        except KeyError:
            self._log.exception("Failed to load module %r for language %r"
                                % (module_name, language))
            raise

        return module


#---------------------------------------------------------------------------
# Create single instance of language loader.
# This instance will be used by code which needs to access language-specific
#  objects, such as the Integer class which retrieves its language-specific
#  content using this language loader.

language = LanguageSpecificLoader()

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
    This file implements a dication formatter for capitalization
    and spacing of dictated text fragments.
"""


try:
	import natlink
except ImportError:
	natlink = None

from ..log import get_log

class Word(object):

    _flag_names = (
        "custom", "undefined", "undefined", "undeletable",
        "cap next", "force cap next", "upper next", "lower next",
        "no space after", "double space after", "no space between", "cap mode",
        "upper mode", "lower mode", "no space mode", "normal space mode",
        "None", "not after period", "no formatting", "keep space",
        "keep cap", "no space before", "normal cap mode", "newline after",
        "double newline after", "no cap in title", "None", "space after",
        "None", "None", "vocab builder", "None"
        )
    _flag_bits = dict(zip(_flag_names, [1 << index for index in xrange(32)]))

    _replacements = {
                     "one":      ("1", 0x00000400),
                     "two":      ("2", 0x00000400),
                     "three":    ("3", 0x00000400),
                     "four":     ("4", 0x00000400),
                     "five":     ("5", 0x00000400),
                     "six":      ("6", 0x00000400),
                     "seven":    ("7", 0x00000400),
                     "eight":    ("8", 0x00000400),
                     "nine":     ("9", 0x00000400),
                    }

    def __init__(self, word):
        if word in self._replacements:
            word, self._info = self._replacements[word]
        else:
            self._info = natlink.getWordInfo(word)
        self._word = word
        index = word.rfind("\\")
        if index == -1:
            self.written = word
            self.spoken = word
        else:
            self.written = word[:index]
            self.spoken = word[index+1:]
        for name, bit in Word._flag_bits.items():
            self.__dict__[name.replace(" ", "_")] = ((self._info & bit) != 0)

    def __str__(self):
        flags = [flag for flag in self._flag_names
            if (self._info & self._flag_bits[flag])]
        flags.insert(0, "")
        return "%s(%r%s)" % (self.__class__.__name__, self._word,
            ", ".join(flags))

class FormatState(object):

    _log = get_log("dictation.formatter")

    (normal, capitalize, upper, lower, force) = range(5)
    (normal, no, double) = range(3)

    def __init__(self):
        self.capitalization = self.normal
        self.capitalization_mode = self.normal
        self.spacing = self.no
        self.spacing_mode = self.normal
        self.between = False

    def apply_formatting(self, word):

        # Capitalize next word.
        c = self.capitalization
        if   c == self.normal or word.no_formatting:
                    written = word.written
        elif c == self.force:   written = word.written.capitalize()
        elif c == self.capitalize:
                    written = word.written.capitalize()
        elif c == self.upper:   written = word.written.upper()
        elif c == self.lower:   written = word.written.lower()
        else: raise ValueError("Unexpected internal state")

        # Determine spacing prefix.
        if   word.no_space_before or word.no_formatting: prefix = ""
        elif self.between and word.no_space_between: prefix = ""
        elif self.spacing == self.normal: prefix = " "
        elif self.spacing == self.no: prefix = ""
        elif self.spacing == self.double: prefix = "  "
        else: raise ValueError("Unexpected internal state")

        # Determine spacing suffix.
        if   word.newline_after: suffix = "\n"
        elif word.double_newline_after: suffix = "\n\n"
        elif word.space_after: suffix = " "
        else: suffix = ""

        return "".join((prefix, written, suffix))

    def update_state(self, word):
        # Process capitalization mode flags of next word.
        if word.normal_cap_mode:    self.capitalization_mode = self.normal
        elif word.cap_mode:     self.capitalization_mode = self.capitalize
        elif word.upper_mode:       self.capitalization_mode = self.upper
        elif word.lower_mode:       self.capitalization_mode = self.lower

        # Process capitalization flags of next word.
        if word.force_cap_next:     self.capitalization = self.force
        elif word.cap_next:     self.capitalization = self.capitalize
        elif word.upper_next:       self.capitalization = self.upper
        elif word.lower_next:       self.capitalization = self.lower
        elif not word.keep_cap:     self.capitalization = self.capitalization_mode

        # Process spacing mode flags of next word.
        if word.no_space_mode:      self.spacing_mode = self.no
        elif word.normal_space_mode:    self.spacing_mode = self.normal

        # Process spacing mode flags of next word.
        if word.no_space_after:     self.spacing = self.no
        elif word.double_space_after:   self.spacing = self.double
        elif not word.keep_space:   self.spacing = self.spacing_mode

        self.between = word.no_space_between

    def format_words(self, words):
        output = []
        for word in words:
            if not isinstance(word, Word): word = Word(word)
            if self._log: self._log.debug("Formatting word: '%s'" % word)
            output.append(self.apply_formatting(word))
            self.update_state(word)
        output = "".join(output)
        if self._log: self._log.debug("Formatted output: '%s'" % output)
        return output

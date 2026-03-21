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
Test suite for English language calendar and time classes
============================================================================

"""

import unittest
from datetime import date, time, timedelta
from unittest.mock import patch

import dragonfly.engines

from dragonfly.engines.backend_text.engine import TextInputEngine
from dragonfly.language.base.integer import Integer
from dragonfly.language.en.number import IntegerContent
from dragonfly.test import ElementTester, RecognitionFailure


def _build_text_engine():
    default_engine = dragonfly.engines._default_engine
    engines_by_name = dragonfly.engines._engines_by_name.copy()
    try:
        return TextInputEngine()
    finally:
        dragonfly.engines._default_engine = default_engine
        dragonfly.engines._engines_by_name = engines_by_name


_ENGINE = _build_text_engine()

_previous_integer_content = Integer._content
Integer._set_content(IntegerContent)
try:
    from dragonfly.language.en.calendar import (AbsoluteDate, MilitaryTime,
                                                RelativeDate,
                                                TwelveHourTime, Year)
finally:
    Integer._content = _previous_integer_content


class EnglishCalendarBoundaryTestCase(unittest.TestCase):

    def _recognize(self, element, words):
        return ElementTester(element, engine=_ENGINE).recognize(words)

    def test_year_upper_bound(self):
        self.assertEqual(2099,
                         self._recognize(Year("year"),
                                         "two thousand ninety nine"))
        self.assertIs(RecognitionFailure,
                      self._recognize(Year("year"),
                                      "two thousand one hundred"))

    def test_absolute_date_day_upper_bound(self):
        self.assertEqual(date(2026, 3, 31),
                         self._recognize(AbsoluteDate("date"),
                                         "March thirty one two thousand "
                                         "twenty six"))
        self.assertIs(RecognitionFailure,
                      self._recognize(AbsoluteDate("date"),
                                      "March thirty two two thousand "
                                      "twenty six"))

    def test_relative_date_day_count_upper_bound(self):
        class FixedDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 3, 21)

        with patch("dragonfly.language.en.calendar.date", FixedDate):
            self.assertEqual(FixedDate.today() + timedelta(days=99),
                             self._recognize(RelativeDate("date"),
                                             "in ninety nine days"))
            self.assertIs(RecognitionFailure,
                          self._recognize(RelativeDate("date"),
                                          "in one hundred days"))

    def test_twelve_hour_minute_upper_bound(self):
        self.assertEqual(time(15, 59),
                         self._recognize(TwelveHourTime("time"),
                                         "three fifty nine PM"))
        self.assertIs(RecognitionFailure,
                      self._recognize(TwelveHourTime("time"),
                                      "three sixty PM"))

    def test_military_time_hour_and_minute_upper_bounds(self):
        self.assertEqual(time(23, 59),
                         self._recognize(MilitaryTime("time"),
                                         "twenty three fifty nine"))
        self.assertIs(RecognitionFailure,
                      self._recognize(MilitaryTime("time"),
                                      "twenty three sixty"))
        self.assertIs(RecognitionFailure,
                      self._recognize(MilitaryTime("time"),
                                      "twenty four hundred"))

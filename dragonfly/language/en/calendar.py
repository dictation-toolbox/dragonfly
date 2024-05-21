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
Date and time elements for the English language
============================================================================

"""

from datetime                         import date, time, timedelta

from dragonfly.grammar.elements       import Alternative, Compound, Choice
from dragonfly.language.base.integer  import Integer, IntegerRef


#---------------------------------------------------------------------------

#names = "January February March April May June July August September October November December".split()
#for index, name in enumerate(names):
#    print '%-13s %2d,' % ('"%s":' % name, index + 1)

month_names = {
               "January":     1,
               "February":    2,
               "March":       3,
               "April":       4,
               "May":         5,
               "June":        6,
               "July":        7,
               "August":      8,
               "September":   9,
               "October":    10,
               "November":   11,
               "December":   12,
              }

day_names   = {
               "Monday":      0,
               "Tuesday":     1,
               "Wednesday":   2,
               "Thursday":    3,
               "Friday":      4,
               "Saturday":    5,
               "Sunday":      6,
              }


#---------------------------------------------------------------------------

class Month(Choice):
    """
        Element allowing one of the twelve months of the year to be
        recognized and used in an action.

    """

    def __init__(self, name):
        Choice.__init__(self, name=name, choices=month_names)


class Day(Choice):
    """
        Element allowing one of the days in a week to be recognized and
        used in an action.

    """
    def __init__(self, name):
        Choice.__init__(self, name=name, choices=day_names)


class Year(Alternative):
    """
        Element allowing a specific calendar year to be recognized and used
        in an action.

        The years 1910 to 2099 may be recognized.

    """
    alts = [
            IntegerRef("year", 2000, 2100),
            Compound(
                     spec="<century> <year>",
                     extras=[Integer("century", 19, 21),
                             IntegerRef("year", 10, 100)],
                     value_func=lambda n, e: e["century"] * 100 + e["year"]
                    ),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)


#---------------------------------------------------------------------------

class AbsoluteDate(Compound):
    """
        Element allowing a date in the current year or in a specific year
        to be recognized and used in an action.

    """

    spec = "(<day> <month> | <month> <day>) [<year>]"
    extras = [IntegerRef("day", 1, 32), Month("month"), Year("year")]

    def __init__(self, name):
        Compound.__init__(self, name=name, spec=self.spec,
                          extras=self.extras)

    def value(self, node):
        month      = node.get_child_by_name("month").value()
        day        = node.get_child_by_name("day").value()
        year_node  = node.get_child_by_name("year")
        if year_node is None:
            today = date.today()
            year = today.year
            if month - today.month > 6:
                # More than six months in the future, use last year.
                year -= 1
            elif month - today.month < -6:
                # More than six months in the past, use next year.
                year += 1
        else:
            year = year_node.value()
        return date(year, month, day)


class RelativeDate(Alternative):
    """
        Element allowing a date relative to the current date to be
        recognized and used in an action.

    """

    class _DayOffset(Choice):
        def __init__(self):
            choices = {
                       "<n> days ago": -1,
                       "yesterday":    -1,
                       "today":         0,
                       "tomorrow":     +1,
                       "in <n> days":  +1,
                      }
            extras = [IntegerRef("n", 1, 100)]
            Choice.__init__(self, name=None, choices=choices, extras=extras)

        def value(self, node):
            value = Choice.value(self, node)
            n = node.get_child_by_name("n")
            #print("November:", n)
            if n is not None:
                value = value * n.value()
            return date.today() + timedelta(days=value)

    class _WeekdayOffset(Choice):
        def __init__(self):
            choices = {
                       "(last | past) <day>":  "last day",
                       "(next | this) <day>":  "next day",
                       "last week <day>":      "last week",
                       "next week <day>":      "next week",
                      }
            extras = [Day("day")]
            Choice.__init__(self, name=None, choices=choices, extras=extras)

        def value(self, node):
            value = Choice.value(self, node)
            day = node.get_child_by_name("day").value()
            now = date.today().weekday()
            #print(value, day, now)
            if value == "last day":
                if day < now:  day_offset = -now + day
                else:          day_offset = -7 - now + day
            elif value == "next day":
                if day < now:  day_offset = 7 - now + day
                else:          day_offset = day - now
            elif value == "last week":
                day_offset = -now - 7 + day
            elif value == "next week":
                day_offset = -now + 7 + day
            return date.today() + timedelta(days=day_offset)

    alts = [
            _DayOffset(),
            _WeekdayOffset(),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)


class Date(Alternative):
    """
        Element allowing either an absolute date or a relative date to be
        recognized and used in an action.

    """

    alts = [
            AbsoluteDate(None),
            RelativeDate(None),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)


#---------------------------------------------------------------------------

class TwelveHourTime(Compound):
    """
        Element allowing twelve-hour time to be recognized and used in an
        action.

        Examples: nine AM, one oh five PM, three thirty PM.

    """

    spec = "<hour> [(<zero> <min_1_10> | <min_10_60>)] <am_pm>"
    extras = [
              Integer("zero", 0, 1),
              Integer("hour", 1, 13),
              IntegerRef("min_1_10", 1, 10),
              IntegerRef("min_10_60", 10, 60),
              Choice("am_pm", {
                  "AM | a.m.": "AM",
                  "PM | p.m.": "PM",
              })
             ]

    def __init__(self, name):
        Compound.__init__(self, name=name, spec=self.spec,
                          extras=self.extras)

    def value(self, node):
        hour = node.get_child_by_name("hour").value()
        am_pm = node.get_child_by_name("am_pm").value()
        if hour < 12:
            if am_pm == "PM":
                hour += 12
        elif am_pm == "AM":
            hour = 0
        if node.has_child_with_name("min_1_10"):
            minute = node.get_child_by_name("min_1_10").value()
        elif node.has_child_with_name("min_10_60"):
            minute = node.get_child_by_name("min_10_60").value()
        else:
            minute = 0
        return time(hour, minute)


class MilitaryTime(Compound):
    """
        Element allowing military time to be recognized and used in an
        action.

        Examples: zero hundred, oh eight hundred, seventeen hundred hours,
        ten oh five, seventeen thirty.

    """

    spec = ("(<zero_oh> | <zero_oh> <hour_0_10> | <hour_10_24>)"
            " (hundred | <zero_oh> <min_1_10> | <min_10_60>) [hours]")
    extras = [
              Integer("zero_oh", 0, 1),
              Integer("hour_0_10", 1, 10),
              Integer("hour_10_24", 10, 24),
              IntegerRef("min_1_10", 1, 10),
              IntegerRef("min_10_60", 10, 60),
             ]

    def __init__(self, name):
        Compound.__init__(self, name=name, spec=self.spec,
                          extras=self.extras)

    def value(self, node):
        if node.has_child_with_name("hour_0_10"):
            hour = node.get_child_by_name("hour_0_10").value()
        elif node.has_child_with_name("hour_10_24"):
            hour = node.get_child_by_name("hour_10_24").value()
        else:
            hour = 0
        if node.has_child_with_name("min_1_10"):
            minute = node.get_child_by_name("min_1_10").value()
        elif node.has_child_with_name("min_10_60"):
            minute = node.get_child_by_name("min_10_60").value()
        else:
            minute = 0
        return time(hour, minute)


class Time(Alternative):
    """
        Element allowing the time of day to be recognized and used in an
        action.

        This allows speaking the twelve-hour time or twenty-four hour
        military time.

    """

    alts = [
            TwelveHourTime(None),
            MilitaryTime(None),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)

#---------------------------------------------------------------------------


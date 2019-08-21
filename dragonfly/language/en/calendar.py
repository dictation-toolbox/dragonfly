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

from datetime import date, time, timedelta
from ...grammar.elements  import Alternative, Compound, Choice
from ..base.integer       import Integer, IntegerRef


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

    def __init__(self, name):
        Choice.__init__(self, name=name, choices=month_names)


class Day(Choice):

    def __init__(self, name):
        Choice.__init__(self, name=name, choices=day_names)


class Year(Alternative):

    alts = [
            IntegerRef("year", 2000, 2100),
            Compound(
                     spec="<century> <year>",
                     extras=[Integer("century", 20, 21),
                             IntegerRef("year", 10, 100)],
                     value_func=lambda n, e: e["century"] * 100 + e["year"]
                    ),
            Compound(
                     spec="<century> <year>",
                     extras=[Integer("century", 19, 20),
                             IntegerRef("year", 1, 100)],
                     value_func=lambda n, e: e["century"] * 100 + e["year"]
                    ),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)


#---------------------------------------------------------------------------

class AbsoluteDate(Compound):

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
            print("November:", n)
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
            print(value, day, now)
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

    alts = [
            AbsoluteDate(None),
            RelativeDate(None),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)


#---------------------------------------------------------------------------

class MilitaryTime(Compound):

    spec = "<hour> (hundred | (oh | zero) <min_1_10> | <min_10_60>)"
    extras = [
              Integer("hour", 0, 25),
              IntegerRef("min_1_10", 1, 10),
              IntegerRef("min_10_60", 10, 60),
             ]

    def __init__(self, name):
        Compound.__init__(self, name=name, spec=self.spec,
                          extras=self.extras)

    def value(self, node):
        hour = node.get_child_by_name("hour").value()
        if node.has_child_with_name("min_1_10"):
            minute = node.get_child_by_name("min_1_10").value()
        elif node.has_child_with_name("min_10_60"):
            minute = node.get_child_by_name("min_10_60").value()
        else:
            minute = 0
        return time(hour, minute)


class Time(Alternative):

    alts = [
            MilitaryTime(None),
           ]

    def __init__(self, name):
        Alternative.__init__(self, name=name, children=self.alts)

#---------------------------------------------------------------------------


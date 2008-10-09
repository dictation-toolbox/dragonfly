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
	This file implements a basic multiplexing interface to the natlink timer.
"""


import time
import natlink


class _Timer(object):

	class Callback(object):
		def __init__(self, function, interval):
			self.function = function
			self.interval = interval
			self.next_time = time.clock() + self.interval
		def call(self):
			self.next_time += self.interval
			self.function()

	def __init__(self, interval):
		self.interval = interval
		self.callbacks = []

	def add_callback(self, function, interval):
		self.callbacks.append(self.Callback(function, interval))
		if len(self.callbacks) == 1:
			natlink.setTimerCallback(self.callback, int(self.interval * 1000))

	def remove_callback(self, function):
		for c in self.callbacks:
			if c.function == function: self.callbacks.remove(c)
		if len(self.callbacks) == 0:
			natlink.setTimerCallback(None, 0)

	def callback(self):
		now = time.clock()
		for c in self.callbacks:
			if c.next_time < now: c.call()


timer = _Timer(0.025)

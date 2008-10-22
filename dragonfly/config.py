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
    This module implements Dragonfly's command module
    configuration framework.
"""

import os.path
import inspect
import textwrap


#---------------------------------------------------------------------------
# Config processing modes:
#  - initializing -- Config is being set up and populated.
#  - loading -- Config setup is complete, loading from user file.
#  - done -- Config initialization and loading complete, ready to use.

_init, _load, _done = range(3)


#---------------------------------------------------------------------------
# Config class; this manages a command module's configuration.

class Config(object):

    def __init__(self, name):
        set_ = object.__setattr__
        set_(self, "name", name)
        set_(self, "_sections", {})
        set_(self, "_sections_list", [])
        set_(self, "_mode", _init)

    def _set_mode(self, mode):
        object.__setattr__(self, "_mode", mode)
        for n, s in self._sections_list:
            s._set_mode(mode)

    def __getattr__(self, name):
        if name in self._sections:  return self._sections[name]
        else:                       raise AttributeError(name)

    def __setattr__(self, name, value):
        if self._mode == _init:
            if isinstance(value, Section):
                self._sections[name] = value
                self._sections_list.append((name, value))
            else: raise TypeError("Invalid type %s, expecting Section."
                                  % type(value))
        else: raise AttributeError(name)



    def load(self, path=None):
        self._set_mode(_load)
        if not path:
            caller_frame = inspect.currentframe().f_back
            caller_file = caller_frame.f_globals["__file__"]
            module_base = os.path.splitext(caller_file)[0]
            path = module_base + ".txt"

        if not os.path.exists(path):
            self._set_mode(_done)
            return

        self.load_from_file(path)
        self._set_mode(_done)

    def load_from_file(self, path):
        namespace = dict(self._sections)
        execfile(path, namespace)

    _comment_wrapper = textwrap.TextWrapper(
                                   width=70,
                                   break_long_words=False,
                                   initial_indent="# ",
                                   subsequent_indent="#  ",
                                  )

    def _format_file_head(self):
        header = "Dragonfly config for %(config_name)s" % {"config_name": self.name}
        lines = self._comment_wrapper.wrap(header)
        lines.insert(0, "#")
        lines.append("#")
        lines.append("")
        return lines

    def _format_section_head(self, name, section, names):
        width = 76
        header = "#--- %s " % section.doc
        length = width - len(header)
        if length > 0: header += "-" * length
        return [header, ""]

    def _format_item(self, name, item, names):
        path = ".".join(list(names) + [name])
        data = {
                "doc":      item.doc,
                "default":  item.default,
                "value":    item.value,
                "path":     path,
               }
        header = "%(doc)s" % data
        lines = self._comment_wrapper.wrap(header)
        lines.append("# Default: %(default)r" % data)
        lines.append("%(path)s = %(value)r" % data)
        lines.append("")
        return lines

    def generate_config_file(self, path=None):
        # Config file header.
        output = self._format_file_head()

        # Iterates through the sections.
        stack = [iter(self._sections_list)]
        names = []
        while stack:
            # Try to retrieve the next section from the top of the stack.
            try: 
                section_name, section = stack[-1].next()
                names.append(section_name)
            except StopIteration:
                # No more subsections, remove section from top of stack.
                # Check for names needed for when the root Config is popped.
                stack.pop()
                if names: names.pop()
                continue

            # Generate section head.
            section_head = self._format_section_head(section_name, section, names)
            output.extend(section_head)

            # Output section items.
            for item_name, item in section._items_list:
                item_output = self._format_item(item_name, item, names)
                output.extend(item_output)

            # Push section onto the stack.
            stack.append(iter(section._sections_list))

        if not path:
            caller_frame = inspect.currentframe().f_back
            caller_file = caller_frame.f_globals["__file__"]
            module_base = os.path.splitext(caller_file)[0]
            path = module_base + ".txt"

        f = open(path, "w")
        f.write("\n".join(output))
        f.close()
        f = None


#---------------------------------------------------------------------------
# Section class; this represents a section within a Config hierarchy.

class Section(object):

    def __init__(self, doc):
        set_ = object.__setattr__
        set_(self, "doc", doc)
        set_(self, "_items", {})
        set_(self, "_items_list", [])
        set_(self, "_sections", {})
        set_(self, "_sections_list", [])
        set_(self, "_mode", _init)

    def _set_mode(self, mode):
        object.__setattr__(self, "_mode", mode)
        for n, s in self._sections_list:
            s._set_mode(mode)

    def __getattr__(self, name):
        if name in self._items:        return self._items[name].value
        elif name in self._sections:   return self._sections[name]
        else:                          raise AttributeError(name)

    def __setattr__(self, name, value):
        if self._mode == _init:
            if isinstance(value, Item):
                self._items[name] = value
                self._items_list.append((name, value))
            elif isinstance(value, Section):
                self._sections[name] = value
                self._sections_list.append((name, value))
            else:
                raise TypeError("Invalid type %s, expecting Item or Section."
                                % type(value))
        elif self._mode == _load:
            if name in self._items:    self._items[name].value = value
            else:                      raise AttributeError(name)
        else:
            raise AttributeError(name)


#---------------------------------------------------------------------------
# Item classes which represent config values.

class Item(object):

    def __init__(self, default, doc):
        self._default = default
        self._value = default
        self.doc = doc

    def get_default(self):
        return self._default

    def get_value(self):
        return self._value

    def set_value(self, value):
        self.validate(value)
        self._value = value

    def validate(self, value):
        if not isinstance(value, type(self._default)):
            raise TypeError("Invalid type %s, expecting %s."
                            % (type(value), type(self._default)))

    value = property(get_value, set_value)
    default = property(get_default)

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
Configuration toolkit
============================================================================

Dragonfly's configuration toolkit makes it very easy to store
program data in a separate file from the main program logic.  It uses
a three-phase *setup -- load -- use* system:

 - *setup* -- a Config object is created and its structure and
   default contents are defined.
 - *load* -- a separate file containing the user's configuration
   settings is looked for and, if found, its values are loaded
   into the Config object.
 - *use* -- the program directly accesses the configuration
   through easy Config object attributes.

This configuration toolkit uses the following three classes:

 - :class:`Config` -- a collection of configuration settings, grouped
   within one or more sections
 - :class:`Section` -- a group of items and/or subsections
 - :class:`Item` -- a single configuration setting

Usage example
----------------------------------------------------------------------------

The main program using Dragonfly's configuration toolkit would
normally look something like this: ::

    from dragonfly import Config, Section, Item

    # *Setup* phase.
    # This defines a configuration object with the name "Example
    #  configuration".  It contains one section with the title
    #  "Test section", which has two configuration items.  Both
    #  these items have a default value and a docstring.
    config                 = Config("Example configuration")
    config.test            = Section("Test section")
    config.test.fruit      = Item("apple", doc="Must eat fruit.")
    config.test.color      = Item("blue", doc="The color of life.")

    # *Load* phase.
    # This searches for a file with the same name as the main program,
    #  but with the extension ".py" replaced by ".txt".  It is also
    #  possible to explicitly specify the configuration file's path.
    #  See Config.load() for more details.
    config.load()

    # *Use* phase.
    # The configuration values can now be accessed through the
    #  configuration object as follows.
    print "The color of life is", config.test.color
    print "You must eat an %s every day" % config.test.fruit

The configuration defined above is basically complete.  Every
configuration item has a default value and can be accessed by
the program.  But if the user would like to modify some or all
of these settings, he can do so in an external configuration file
without modifying the main program code.

This external configuration file is interpreted as Python code.
This gives its author powerful tools for determining the desired
configuration settings.  However, it will usually consist merely
of variable assignments. The configuration file for the program
above might look something like this: ::

    # Test section
    test.fruit = "banana"   # Bananas have more potassium.
    test.color = "white"    # I like light colors.


Example command modules
----------------------------------------------------------------------------

The configuration toolkit is utilized in a number of command modules in the
*t4ngo/dragonfly-modules* repository, available on GitHub.  See
:ref:`Related Resources: Command modules <RefCommandModulesList>`.


Implementation details
----------------------------------------------------------------------------

This configuration toolkit makes use of Python's special methods
for setting and retrieving object attributes.  This makes it much
easier to use, as there is no need to use functions such as
*value = get_config_value("item_name")*; instead the configuration
values are immediately accessible as Python objects.  It also allows
for more extensive error checking; it is for example trivial to
implement custom *Item* classes which only allow specific values
or value types, such as integers, boolean values, etc.


Configuration class reference
----------------------------------------------------------------------------

"""

import sys
import os.path
import inspect
import textwrap
import traceback

import logging


#---------------------------------------------------------------------------
# Config processing modes:
#  - initializing -- Config is being set up and populated.
#  - loading -- Config setup is complete, loading from user file.
#  - done -- Config initialization and loading complete, ready to use.

_init, _load, _done = range(3)


#---------------------------------------------------------------------------
# Config class; this manages a command module's configuration.

class Config(object):
    """
        Configuration class for storing program settings.

        Constructor argument:
         - *name* (*str*) --
           the name of this configuration object.

        This class can contain zero or more :class:`Section` instances,
        each of which can contain zero or more :class:`Item` instances.
        It is these items which store the actual configuration settings.
        The sections merely divide the items up into groups, so that
        different configuration topics can be split for easy readability.

  """

    _configs_by_name = {}
    _log = logging.getLogger("config")


    #-----------------------------------------------------------------------

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls._configs_by_name[name]
        except KeyError:
            return None

    @classmethod
    def get_instances(cls):
        instances = list(cls._configs_by_name.items())
        instances.sort()
        return [instance for name, instance in instances]


    #-----------------------------------------------------------------------

    def __init__(self, name):
        set_ = object.__setattr__
        set_(self, "name", name)
        set_(self, "_sections", {})
        set_(self, "_sections_list", [])
        set_(self, "_mode", _init)
        set_(self, "module_path", None)
        set_(self, "config_path", None)

        Config._configs_by_name[name] = self

    def _set_mode(self, mode):
        object.__setattr__(self, "_mode", mode)
        for n, s in self._sections_list:
            s._set_mode(mode)

    def __getattr__(self, name):
        if name in self._sections:
            return self._sections[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if self._mode == _init:
            if isinstance(value, Section):
                self._sections[name] = value
                self._sections_list.append((name, value))
            else: raise TypeError("Invalid type %s, expecting Section."
                                  % type(value))
        else: raise AttributeError(name)


    def load(self, path=None):
        """
            Load the configuration file at the given *path*, or
            look for a configuration file associated with the calling
            module.

             - *path* (*str*, default: *None*) --
               path to the configuration file to load.  If *None*,
               then a path is generated from the calling module's
               file name by replacing its extension with ".txt".

            If the *path* is a file, it is loaded.  On the other hand,
            if it does not exist or is not a file, nothing is loaded
            and this configuration's defaults remain in place.

        """
        self._set_mode(_load)
        if not path:
            caller_frame = inspect.currentframe().f_back
            caller_file = caller_frame.f_globals["__file__"]
            module_base, module_ext = os.path.splitext(caller_file)
            path = module_base + ".txt"
            if module_ext in (".pyc", ".pyo"):
                module_ext = ".py"
            object.__setattr__(self, "module_path", module_base + module_ext)
        object.__setattr__(self, "config_path", path)

        if os.path.exists(path):
            namespace = self.load_from_file(path)
        else:
            namespace = None
        self._set_mode(_done)

        return namespace

    def load_from_file(self, path):
        namespace = dict(self._sections)
        for name, section in self._sections_list:
            section.update_namespace(namespace)

        try:
            with open(path) as file:
                exec(compile(file.read(), path, 'exec'), namespace)
#        except ConfigError, e:
        except Exception as e:
            print("exception:", e)
            t, v, tb = sys.exc_info()
            frames = traceback.extract_tb(tb)
            relevant_frames = []
            error_line = "<unknown>"
            include_all = False
            for frame in frames:
                filename, line, function, text = frame
                print("frame:", frame)

                if not include_all:
                    file1 = os.path.basename(filename)
                    file2 = os.path.basename(path)
                    if file1 == file2:
                        include_all = True
                        error_line = line

                if include_all:
                    relevant_frames.append(frame)

            self._log.error("An error occurred in the %s file at line %s."
                            % (path, error_line))
            self._log.error("The error message was: %s" % e)
            formatted = traceback.format_list(relevant_frames)
            lines = "\n".join(formatted).splitlines()
            for line in lines:
                self._log.error("    " + line)

        return namespace

    _comment_indent = " "*20
    _comment_wrapper = textwrap.TextWrapper(
                                   width=70,
                                   break_long_words=False,
                                   initial_indent=_comment_indent+"# ",
                                   subsequent_indent=_comment_indent+"#  ",
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
        lines = []
        lines.append("%(path)s = %(value)r" % data)
        if item.doc:
            header = "%(doc)s" % data
            lines.extend(self._comment_wrapper.wrap(header))
            lines.extend(self._comment_wrapper.wrap("Default: %(default)r" % data))
        lines.append("")
        return lines

    def generate_config_file(self, path=None):
        """
            Create a configuration file containing this
            configuration object's current settings.

             - *path* (*str*, default: *None*) --
               path to the configuration file to load.  If *None*,
               then a path is generated from the calling module's
               file name by replacing its extension with ".txt".

        """
        # Config file header.
        output = self._format_file_head()

        # Iterates through the sections.
        stack = [iter(self._sections_list)]
        names = []
        while stack:
            # Try to retrieve the next section from the top of the stack.
            try:
                section_name, section = next(stack[-1])
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
    """
        Section of a configuration for grouping items.

        Constructor argument:
         - *doc* (*str*) --
           the name of this configuration section.

        A section can contain zero or more subsections and zero or more
        configuration items.

    """

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

    def update_namespace(self, namespace):
        for name, item in self._items_list:
            item.update_namespace(namespace)
        for name, section in self._sections_list:
            section.update_namespace(namespace)


#---------------------------------------------------------------------------
# Item classes which represent config values.

class Item(object):
    """
        Configuration item for storing configuration settings.

        Constructor arguments:
         - *default* --
           the default value for this item
         - *doc* (*str*, default: *None*) --
           an optional description of this item
         - *namespace* (*dict*, default: *None*) --
           an optional namespace dictionary which will be made available
           to the Python code in the external configuration file
           during loading

        A configuration item is the object that stores the actual
        configuration settings.  Each item has a default value, a current
        value, an optional description, and an optional namespace.

        This class performs the checking of configuration values assigned
        to it during loading of the configuration file.  The default
        behavior of this class is to only accept values of the same Python
        type as the item's default value.  So, if the default value is a
        string, then the value assigned in the configuration file must
        also be a string.  Otherwise an exception will be raised and
        loading will fail.

        Developers who want other kinds of value checking should override
        the :meth:`Item.validate` method of this class.

    """


    def __init__(self, default, doc=None, namespace=None):
        self._default = default
        self._value = default
        self.doc = doc
        self._namespace = namespace

    def get_default(self):
        return self._default

    def get_value(self):
        return self._value

    def set_value(self, value):
        self.validate(value)
        self._value = value

    def validate(self, value):
        """
            Determine whether the given *value* is valid.

            This method performs validity checking of the configuration
            value assigned to this item during loading of the external
            configuration file.  If the default behavior is to raise a
            *TypeError* if the type of the assigned value is not the same
            as the type of the default value.

        """
        if not isinstance(value, type(self._default)):
            raise TypeError("Invalid type %s, expecting %s."
                            % (type(value), type(self._default)))

    value = property(get_value, set_value)
    default = property(get_default)

    def update_namespace(self, namespace):
        if self._namespace:
            namespace.update(self._namespace)

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
Loader
============================================================================

"""

import os.path
import glob
import time
import configparser
import collections
from collections import defaultdict

import dragonfly
from ...error                    import DragonflyError
from ...grammar.rule_base        import Rule
from ...grammar.context          import AppContext
from ...actions                  import ActionBase
from ...parser                   import Parser
from .dirmon                     import DirectoryMonitor
from .family                     import CommandFamily
from .state                      import StateBase as State
from .state                      import Transition
from .command                    import CompoundCommand
from .loader_parser              import CallElement


#===========================================================================
# Exception classes.

class LoaderError(DragonflyError):
    pass

class SyntaxError(LoaderError):
    pass


#===========================================================================
# Container base class similar to C's struct.

class ContainerBase(object):

    _attributes = ()

    def __init__(self, **kwargs):
        for name, default in self._attributes:
            if name in kwargs:       value = kwargs.pop(name)
            elif isinstance(default, collections.Callable):  value = default()
            else:                    value = default
            setattr(self, name, value)
        if kwargs:
            names = sorted(kwargs.keys())
            raise ValueError("Unknown keyword args: %s" % names)


#===========================================================================
# Input information storage classes.

class InfoPhase1(ContainerBase):

    class InfoPhase1Section(ContainerBase):
        _attributes = (
                       ("tag",           None),
                       ("items",         dict),
                      )

    _attributes = (
                   ("sections", lambda: defaultdict(InfoPhase1.InfoPhase1Section)),
                  )


class InfoPhase2(ContainerBase):

    class InfoPhase2Family(ContainerBase):
        _attributes = (
                       ("tag",           None),
                       ("name",          None),
                       ("description",   None),
                       ("states",        dict),
                       ("extras",        list),
                      )
    class InfoPhase2Choice(ContainerBase):
        _attributes = (
                       ("pairs",         None),
                      )

    _attributes = (
                   ("families", lambda: defaultdict(InfoPhase2.InfoPhase2Family)),
                   ("choices",  lambda: defaultdict(InfoPhase2.InfoPhase2Choice)),
                  )


#===========================================================================
# Config parser class.

class CommandConfigParser(configparser.RawConfigParser):
    """ Customized ConfigParser class for parsing command files. """

    def optionxform(self, option):
        """
            Return option-string unchanged.

            This overrides the default behavior of converting the 
            option-string to lowercase.

        """
        return option


#===========================================================================
# Structured container classes for storing config file input.

class ConfigSection(object):

    def __init__(self, name, items):
        self._section_name = name
        self._section_items = items
        self._parse_name(self._section_name)
        self._parse_items(self._section_items)

    def _parse_name(self, name):
        pass

    def _parse_items(self, items):
        pass

    def _split_name_type_tag(self, name):
        sep_index = name.find(":")
        if sep_index == -1:
            raise Exception("Invalid section name: %r" % name)
        section_type = name[:sep_index].strip().lower()
        section_tag = name[sep_index+1:].strip().lower()
        if not section_type or not section_tag:
            raise Exception("Invalid section name: %r" % name)
        return section_type, section_tag

    def _split_name_type_family_tag(self, name):
        section_type, family_section_tag = self._split_name_type_tag(name)
        sep_index = family_section_tag.find(".")
        if sep_index == -1:
            raise Exception("Invalid section name: %r" % name)
        family_tag = family_section_tag[:sep_index].strip().lower()
        if not family_tag:
            raise Exception("Invalid section name: %r" % name)
        return section_type, family_tag, family_section_tag

    def _build_items_dict(self, items, error_on_duplicate_key=True):
        items_dict = {}
        for key, value in items:
            if key in items_dict:
                if error_on_duplicate_key:
                    raise Exception("Duplicate key: %r" % key)
                continue
            items_dict[key] = value
        return items_dict

    def _unescape_spoken_form(self, escaped):
        escaped = escaped.strip()
        if escaped[0] != '"' or escaped[-1] != '"':
            raise Exception("Invalid spoken form: %r" % escaped)
        unescaped = escaped[1:-1]
        return unescaped


class FamilySection(ConfigSection):

    def _parse_name(self, name):
        section_type, family_tag = self._split_name_type_tag(name)
        self.tag = family_tag

    def _parse_items(self, items):
        items_dict = self._build_items_dict(items)

        # Parse "name" item, if present.
        if "name" in items_dict:
            name_string = items_dict.pop("name")
            self.name = name_string.strip()
        else:
            raise Exception("Family section %r missing name item."
                            % self._section_name)

        # Parse "description" item, if present.
        if "description" in items_dict:
            description_string = items_dict.pop("description")
            self.description = description_string.strip()
        else:
            self.description = None

        # Parse "length" item, if present.
        if "length" in items_dict:
            length_string = items_dict.pop("length")
            self.length = int(length_string)
        else:
            self.length = 4

        if items_dict:
            raise Exception("Family section contains invalid items:"
                            " %s" % (sorted(items_dict.keys()),))


class StateSection(ConfigSection):

    def _parse_name(self, name):
        section_type, family_tag, tag = self._split_name_type_family_tag(name)
        self.family_tag = family_tag
        self.tag = tag

    def _parse_items(self, items):
        items_dict = self._build_items_dict(items)

        # Parse "name" item, if present.
        if "name" in items_dict:
            self.name = items_dict.pop("name")
        else:
            self.name = self.tag

        # Parse "include" item, if present.
        if "include" in items_dict:
            include_string = items_dict.pop("include")
            include_names = [s.strip() for s in include_string.split(",")]
            self.include = include_names
        else:
            self.include = ()

        # Parse "context" item, if present.
        if "context" in items_dict:
            context_string = items_dict.pop("context")
            self.context = context_string.strip()
        else:
            raise Exception("State section %r missing context item."
                            % self._section_name)

        # Parse "next" item, if present.
        if "next" in items_dict:
            next_string = items_dict.pop("next")
            self.next = next_string.strip()
        else:
            self.next = None

        self.commands = []
        for spoken, spec in items_dict.items():
            spoken = self._unescape_spoken_form(spoken)
            self.commands.append((spoken, spec))


class ExtrasSection(ConfigSection):

    def _parse_name(self, name):
        section_type, family_tag = self._split_name_type_tag(name)
        self.tag = family_tag

    def _parse_items(self, items):
        self.extras = []
        for item in items:
            key, spec = item
            self.extras.append((key, spec))


class ChoiceSection(ConfigSection):

    def _parse_name(self, name):
        section_type, family_tag = self._split_name_type_tag(name)
        self.tag = family_tag

    def _parse_items(self, items):
        self.choices = []
        for item in items:
            spoken, spec = item
            self.choices.append((spoken, spec))


class InputSpec(object):
        pass


class InputInfo(ContainerBase):

    _attributes = (
                   ("family_sections",  None),
                   ("family_states",    None),
                   ("family_extras",    None),
                   ("choice_sections",  None),
                  )


#===========================================================================

class Loader(object):

    _extras_factories = {}

    @classmethod
    def register_extras_factory(cls, extra_type, factory):
        cls._extras_factories[extra_type] = factory

    def __init__(self):
        self._dirmon = DirectoryMonitor()
        self._loaded = False
        self._families = []

    def add_directories(self, *directories):
        """
            Add one or more directories to be monitored.

            Parameter:
              - directories (sequence of *str* or *unicode*) --
                the new directories to be monitored.

        """
        self._dirmon.add_directories(*directories)

    #-----------------------------------------------------------------------

    def load(self):
        """ Load families found in monitored directories. """
        self._loaded = True

        # Find files to be loaded.
        directories = self._dirmon.directories
        command_files = self._find_command_files(directories)
        library_files = self._find_library_files(directories)
#        print "command files", command_files
#        print "library files", library_files

        # Read and parse command files.
        input_spec = self._parse_command_files(command_files)

        # Load family objects into engine.
        for family in self._families:
            family.load()

    def unload(self):
        """ Unload all commands. """
        for family in self._families:
            family.unload()
        self._loaded = False

    def check_for_changes(self):
        """
            Check for changes and reload if necessary.

            Return *True* if files were reloaded; otherwise *False*.

        """
        if not self._loaded or not self._dirmon.is_modified():
            return False
        self.unload()
        self.load()
        return True

    #-----------------------------------------------------------------------

    def _find_command_files(self, directories):
        return self._glob_files_in_directories(directories, "*.txt")

    def _find_library_files(self, directories):
        return self._glob_files_in_directories(directories, "*.py")

    def _glob_files_in_directories(self, directories, pattern):
        files = []
        for directory in directories:
            directory_pattern = os.path.join(directory, pattern)
            files.extend(glob.glob(directory_pattern))
        return files

        for directory in directories:
            for filename in os.listdir(directory):
                extension = os.path.splitext(filename)[1]
                if extension.lower() == ".txt":
                    files.append(os.path.join(directory, filename))

    def _parse_command_files(self, command_files):
        # Create config parser and read command files.
        config = CommandConfigParser()
        for path in command_files:
            config.read(path)

        dispatchers = {
                       "family:":   FamilySection,
                       "state:":    StateSection,
                       "extras:":   ExtrasSection,
                       "choice:":   ChoiceSection,
                      }

        # Iterate over all input sections and process each according
        #  to the section name's prefix.
        sections = []
        for section_name in config.sections():
            items = config.items(section_name)
            cooked_name = section_name.strip().lower()
            section_instance = None
            for prefix, section_class in dispatchers.items():
                if cooked_name.startswith(prefix):
                    section_instance = section_class(section_name, items)
                    break
            if not section_instance:
                raise Exception("Invalid section: %r" % section_name)
            sections.append(section_instance)

        # Iterate over all processed section objects and handle each
        #  according to its type.
        family_sections = {}
        family_states   = {}
        family_extras   = {}
        choice_sections = {}
        for section in sections:
            if isinstance(section, FamilySection):
                family_sections[section.tag] = section
            elif isinstance(section, StateSection):
                states = family_states.setdefault(section.family_tag, {})
                states[section.tag] = section
            elif isinstance(section, ExtrasSection):
                family_extras[section.tag] = section
            elif isinstance(section, ChoiceSection):
                choice_sections[section.tag] = section
            else:
                raise Exception("Invalid section type: %r" % section_name)
        input_info = InputInfo(
                               family_sections  = family_sections,
                               family_states    = family_states,
                               family_extras    = family_extras,
                               choice_sections  = choice_sections,
                              )

        # Iterate over all family sections and construct each family.
        families = []
        for family_section in family_sections.values():
            print("constructing family", family_section.tag)
            family = CommandFamily(name=family_section.name)

            extras_section = family_extras[family_section.tag]
            print("  constructing extras", extras_section.tag, extras_section._section_name)
            self._build_family_extras(family, extras_section, input_info)

            states_by_tag = self._init_family_states(family, family_section, input_info)
            for state_section in family_states[family_section.tag].values():
                print("  constructing state", state_section.tag)
#                self._build_family_state(family, state_section, states_by_tag, input_info)

            families.append(family)
        return families

    def _build_family_extras(self, family, extras_section, input_info):
        element = CallElement()
        parser = Parser(element)
        for key, spec in extras_section.extras:
            print("building extra", key, spec)

            # Parse the input spec.
            output = parser.parse(spec)
            output.name = key
            print("output:", output)
            if not output:
                raise SyntaxError("Invalid extra %r: %r" % (key, spec))

            # Look for an appropriate extras factory and let it
            #  build the extra element.
            if output.function not in self._extras_factories:
                raise SyntaxError("Unknown extra type %r in %r" % (output.function, spec))
            factory = self._extras_factories[output.function]
            extra = factory.build(output)

            family.add_extras(extra)

    def _init_family_states(self, family, family_section, input_info):
        sections = list(input_info.family_states[family_section.tag].values())
        states = []
        states_by_tag = {}
        for section in sections:
            state = State(section.name)
            states.append(state)
            states_by_tag[section.tag] = state
        family.add_states(*states)
        return states_by_tag

    def _build_family_state_phase2(self, family, state_section, states_by_tag, input_info):
        state = family.states[state_section.tag]

        context = self._build_state_context(state_section.context)
#        state.set_context(context)

        for state_name in state_section.include:
            included_state = states_by_tag[state_name]
            state.include_states(included_state)

        extras = []

        for spoken, spec in state_section.commands:
            command, poststate_name = self._build_state_command(spoken, spec, extras)
            if not poststate_name:
                poststate = state
            else:
                poststate = states_by_tag[poststate_name]
            transition = Transition(command, state, poststate)
            state.add_transitions(transition)

    def _build_state_context(self, context_spec):
        pass

    def _build_state_command(self, spoken_form, command_spec, extras):
        # Prepare namespace in which to evaluate command_spec.
        namespace = {
#                     "__file__":  path,
#                     "library":   library,
                    }
        for (key, value) in dragonfly.__dict__.items():
            if isinstance(value, type) and issubclass(value, ActionBase):
                namespace[key] = value
        namespace["Repeat"] = dragonfly.Repeat

        # Evaluate command specification.
        expression = "(%s)" % command_spec
        action = eval(expression, namespace, namespace)

        # Wrapup action in extras in a compound command.
        result = (CompoundCommand(spoken_form, action, extras=extras), None)
        return result


#===========================================================================

class ExtrasFactoryBase(object):

    def __init__(self):
        pass

    def build(self, call_info):
        pass


#---------------------------------------------------------------------------

class DictationExtrasFactory(ExtrasFactoryBase):

    def build(self, call_info):
        name = call_info.name
        if call_info.arguments:
            raise SyntaxError("Invalid arguments for dictation extra: %r"
                              % (call_info.arguments,))
        print("just build", dragonfly.Dictation(name))
        return dragonfly.Dictation(name)

Loader.register_extras_factory("dictation", DictationExtrasFactory())


#---------------------------------------------------------------------------

class IntegerExtrasFactory(ExtrasFactoryBase):

    def build(self, call_info):
        name = call_info.name
        min = call_info.arguments.pop().value
        max = call_info.arguments.pop().value
        if call_info.arguments:
            raise SyntaxError("Invalid arguments for integer extra: %r"
                              % (call_info.arguments,))
        print("just build", dragonfly.Integer(name=name, min=min, max=max))
        return dragonfly.Integer(name=name, min=min, max=max)

Loader.register_extras_factory("integer", IntegerExtrasFactory())


#===========================================================================

class ExtrasFactoryError(Exception):
    pass

class ContextFactoryError(Exception):
    pass

class ActionFactoryError(Exception):
    pass

class ContextFactoryBase(object):
    pass

class ActionFactoryBase(object):
    pass

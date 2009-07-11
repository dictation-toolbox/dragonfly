
import os.path
import glob
import time
import ConfigParser
import dragonfly
from ...grammar.rule_base        import Rule
from ...grammar.context          import AppContext
from ...actions                  import ActionBase
from .dirmon                     import DirectoryMonitor
from .family                     import CommandFamily
from .state                      import StateBase as State
from .state                      import Transition
from .command                    import CompoundCommand


#===========================================================================
# Config parser class.

class CommandConfigParser(ConfigParser.RawConfigParser):
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

    def _parse_items(self, items):
        pass

    def _parse_name(self, name):
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
                            " %r" % (items_dict.keys(),))


class StateSection(ConfigSection):

    def _parse_name(self, name):
        section_type, family_tag, tag = self._split_name_type_family_tag(name)
        self.family_tag = family_tag
        self.tag = tag

    def _parse_items(self, items):
        items_dict = self._build_items_dict(items)

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


#===========================================================================

class Loader(object):

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
        print "command files", command_files
        print "library files", library_files

        # Read and parse command files.
        input_spec = self._parse_command_files(command_files)

        # Build family objects.
        families = self._build_families(input_spec)

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

        for family_section in family_sections.values():
            print "constructing family", family_section.tag
            extras_section = family_extras[family_section.tag]
            print "  constructing extras", extras_section.tag, extras_section._section_name
            for state_section in family_states[family_section.tag].values():
                print "  constructing states", state_section.tag

        input_spec = InputSpec()
        input_spec.family_sections = family_sections
        input_spec.family_states = family_states
        input_spec.family_extras = family_extras
        input_spec.choice_sections = choice_sections

        return input_spec

    def _build_families(self, input_spec):
        families = []
        for family_section in input_spec.family_sections.values():
            print "constructing family", family_section.tag

            family = CommandFamily(family_section.name)

            extras_section = input_spec.family_extras[family_section.tag]
            self._build_family_extras(family, extras_section)

            states_by_tag = input_spec.family_states[family_section.tag]
            for state_section in states_by_tag.values():
                print "  constructing states", state_section.tag
                self._build_family_state(family, state_section,
                                         states_by_tag)

            pass

            families.append(family)
        return families

    def _build_family_extras(self, family, extras_section):
        for key, spec in extras_section.extras:
            print "building extra", key, spec

    def _build_family_state(self, family, state_section, states_by_tag):
        state = State(state_section.tag)

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

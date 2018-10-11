
import time
from collections          import defaultdict
from ...grammar.elements  import Compound
import logging


#===========================================================================

class CommandSet(object):

    def __init__(self, commands=None):
        if commands == None:  self._commands = []
        else:                 self._commands = commands

    @property
    def commands(self):
        if self._commands == None:
            return ()
        else:
            return tuple(self._commands)

    def get_poststate_commands_pairs(self):
        mapping = defaultdict(list)
        ids = {}
        for command in self._commands:
            key = id(command.poststate)
            mapping[key].append(command)
            ids[key] = command.poststate
        return [(ids[k], cmds) for (k, cmds) in mapping.items()]

    def add_command(self, command):
        self._commands.append(command)

    def remove_command(self, command):
        if not self._commands:
            return
        try:
            self._commands.remove(command)
        except Exception:
            pass

    def add_commands(self, *commands):
        self._commands.extend(commands)


#===========================================================================

class CommandBase(object):

    _log = logging.getLogger("Command")

    def __init__(self):
        pass

    def __str__(self):
        return "%s()" % (self.__class__.__name__)

    @property
    def element(self):
        raise NotImplementedError("Virtual property %r of class %s."
                                  % ("element", self.__class__.__name__))

    def execute(self, node):
        raise NotImplementedError("Virtual property %r of class %s."
                                  % ("execute", self.__class__.__name__))


#---------------------------------------------------------------------------

class CompoundCommand(CommandBase):

    def __init__(self, spec, action, extras=None):
        CommandBase.__init__(self)
        if extras:  extras = list(extras)
        else:       extras = []
        if isinstance(action, ExtendedAction):
            self._action = action.action
            extras.extend(action.extras)
        else:
            self._action = action
        self._spec = spec
        self._extras = extras
        self._element = Compound(spec, extras=extras)
        CommandBase.__init__(self)

    def __str__(self):
        args = self._spec
        return "%s(%s)" % (self.__class__.__name__, args)

    @property
    def element(self):
        return self._element

    def execute(self, node):
#        self._log.warning("executing CompoundCommand: %s" % node.words())

        extras = {"_node": node}
        for element in self._extras:
            name = element.name
            extra_node = node.get_child_by_name(name, shallow=True)
            if extra_node:
                extras[name] = extra_node.value()
            elif element.has_default():
                extras[name] = element.default

        bound_action = self._action.copy_bind(extras)
        bound_action.execute()


#---------------------------------------------------------------------------

class ExtendedAction(object):
    def __init__(self, action, extras):
        self.action = action
        self.extras = extras

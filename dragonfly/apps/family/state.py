
import time
from collections  import defaultdict
from ...grammar.rule_base import Rule
from ...grammar.context import AppContext
from ...windows.window import Window
from ...actions.action_base import ActionError


#===========================================================================

class StateBase(object):

    toplevel = True

    def __init__(self, name=None):
        self._name = name
        self._transitions = []
        self._include_states = []
        self._command_chain_rules = {}
        self._recursing_transitions = False

    def __str__(self):
        return "%s(name=%s)" % (self.__class__.__name__, self._name)

    #-----------------------------------------------------------------------

    def _get_name(self):
        return self._name
    def _set_name(self, name):
        self._name = name
    name = property(_get_name, _set_name)

    @property
    def transitions(self):
        if self._recursing_transitions:
            return ()
        self._recursing_transitions = True
        try:
            transitions = self._transitions
            for state in self._include_states:
                for transition in state.transitions:
                    transitions.append(transition.copy_with_prestate(self))
        finally:
            self._recursing_transitions = False
        return transitions

    def add_transitions(self, *transitions):
        for transition in transitions:
            if transition not in self._transitions:
                self._transitions.append(transition)

    def include_states(self, *states):
        for state in states:
            if state not in self._include_states:
                self._include_states.append(state)

    #-----------------------------------------------------------------------

    def get_command_chain_rule(self, length, toplevel=False):
        try:
            rule = self._command_chain_rules[length]
        except KeyError:
            chain_element = self._build_command_chain(length)
            global unique; unique += 1
            name = "_%s_%d_%03d" % (self, length, unique-1)
            if toplevel:
                rule = ToplevelRule(element=chain_element, name=name)
            else:
                rule = Rule(element=chain_element, name=name)
            self._command_chain_rules[length] = rule
        return rule

    def _build_command_chain(self, length):
        if length < 1:
            return None
        elif length == 1:
            poststate_ref_pairs = self._build_poststate_ref_pairs()
            alternatives = [ref for pstate, ref in poststate_ref_pairs]
            return Alternative(alternatives)
        else:
            poststate_ref_pairs = self._build_poststate_ref_pairs()
            alternatives = []
            for pstate, ref in poststate_ref_pairs:
                tail = pstate.get_command_chain_rule(length - 1)
                pstate_element = Sequence([ref, Optional(RuleRef(tail))])
                alternatives.append(pstate_element)
            return Alternative(alternatives)

    def _build_poststate_ref_pairs(self):
        poststate_mapping = defaultdict(list)
        poststate_id_mapping = {}
        for command_set in self.command_sets:
            pairs = command_set.get_poststate_commands_pairs()
            for poststate, commands in pairs:
                if not poststate:
                    poststate = self
                poststate_mapping[id(poststate)].extend(commands)
                poststate_id_mapping[id(poststate)] = poststate
        poststate_ref_pairs = []
        for poststate_id, commands in poststate_mapping.items():
            poststate = poststate_id_mapping[poststate_id]
            command_refs = [CommandRef(cmd, self) for cmd in commands]
            command_element = Alternative(command_refs)
            global unique; unique += 1
            name = "_%s_%s_%03d" % (self, poststate, unique-1)
            command_rule = Rule(element=command_element, name=name)
            poststate_ref_pairs.append((poststate, RuleRef(command_rule)))
        return poststate_ref_pairs

    #-----------------------------------------------------------------------

    def is_active(self):
        return False

    def is_active_toplevel(self):
        return self.is_active()


#---------------------------------------------------------------------------

class GlobalState(StateBase):

    def __init__(self):
        StateBase.__init__(self)

    def is_active(self):
        return True


#---------------------------------------------------------------------------

class StopState(StateBase):

    toplevel = False

    def __init__(self):
        StateBase.__init__(self)

    def is_active(self):
        return False


#---------------------------------------------------------------------------

class HiddenState(StateBase):

    toplevel = False

    def __init__(self):
        StateBase.__init__(self)

    def is_active(self):
        return True

    def is_active_toplevel(self):
        return False


#---------------------------------------------------------------------------

class WindowState(StateBase):

    def __init__(self, executable=None, title=None):
        StateBase.__init__(self)
        self._executable  = executable
        self._title       = title
        self._context     = AppContext(executable=executable, title=title)

    def __str__(self):
        args = []
        if self._executable:  args.append(self._executable)
        if self._title:       args.append(self._title)
        args = ",".join(args)
        return "%s(%s)" % (self.__class__.__name__, args)

    def is_active(self):
        window = Window.get_foreground()
        return self._context.matches(
                                     executable=window.executable,
                                     title=window.title,
                                     handle=window.handle,
                                    )


#===========================================================================

class Transition(object):

    def __init__(self, command, prestate, poststate):
        self._command    = command
        self._prestate   = prestate
        self._poststate  = poststate
        self._timeout    = 1.0
        self._interval   = 0.1

    @property
    def prestate(self):
        return self._prestate

    @property
    def poststate(self):
        return self._poststate

    @property
    def command(self):
        return self._command

    def copy_with_prestate(self, prestate):
        clone = Transition(self._command, prestate, self._poststate)
        return clone

    def bind(self, node):
        return BoundTransition(self, node)

    def execute(self, node):
        timeout_time = time.time() + self._timeout
        while not self.prestate.is_active():
            if time.time() > timeout_time:
                raise ActionError("prestate not active: %s" % self.prestate)
            time.sleep(self._interval)
        self._command.execute(node)


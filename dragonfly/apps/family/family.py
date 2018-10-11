

from collections                import defaultdict
from ...grammar.grammar_base    import Grammar
from ...grammar.rule_base       import Rule
from ...grammar.elements_basic  import (Sequence, Alternative, RuleRef,
                                        Optional)


#===========================================================================

class CommandFamily(Grammar):

    def __init__(self, name):
        Grammar.__init__(self, name)
        self._extras = []
        self._states = []
        self._toplevel_rules = ()
        self._previous_details = None

    #-----------------------------------------------------------------------

    @property
    def states(self):
        return tuple(self._states)

    def add_states(self, *states):
        self._states.extend(states)

    @property
    def extras(self):
        return tuple(self._extras)

    def add_extras(self, *extras):
        self._extras.extend(extras)

    #-----------------------------------------------------------------------

    def _build_transition_web(self):
        # Build a list of all transitions within this family.
        transitions = []
        for state in self.states:
            transitions.extend(state.transitions)

        # Build a mapping of prestate -> poststate -> list of transitions.
        mapping = defaultdict(lambda: defaultdict(list))
        ids = {}
        for transition in transitions:
            pre_key       = id(transition.prestate)
            post_key      = id(transition.poststate)
            ids[pre_key]  = transition.prestate
            ids[post_key] = transition.poststate
            mapping[pre_key][post_key].append(transition)

#        # DEBUGGING output.
#        for pre_key, inner_mapping in mapping.items():
#            print "pre-state: %s" % ids[pre_key]
#            for post_key, transitions in inner_mapping.items():
#                print "  post-state: %s" % ids[post_key]
#                for transition in transitions:
#                    print "    command: %s" % transition.command

        # Build transition-web container.
        web = {}
        for pre_key, inner_mapping in mapping.items():
            pre_state = ids[pre_key]
            post_state_transitions_pairs = []
            for post_key, transitions in inner_mapping.items():
                post_state = ids[post_key]
                pair = (post_state, transitions)
                post_state_transitions_pairs.append(pair)
            web[pre_key] = (pre_state, post_state_transitions_pairs)

        return web

    def _build_transition_rules(self, web):
        transition_rules = {}
        for (pre_state, post_state_transitions_pairs) in web.values():
            for (post_state, transitions) in post_state_transitions_pairs:
                rule = TransitionsRule(transitions, pre_state, post_state)
                key = (id(pre_state), id(post_state))
                transition_rules[key] = rule
        return transition_rules

    def _build_toplevel_rules(self, web, transition_rules, length):
        toplevel_rules = []
        for (pre_state, post_state_transitions_pairs) in web.values():
            if not pre_state.toplevel:
                continue
            tree = self._build_transition_tree(pre_state, web, length)
            element = self._build_tree_element(tree, transition_rules)
            rule = ToplevelRule(element, pre_state)
            toplevel_rules.append(rule)
        return toplevel_rules

    def _build_transition_tree(self, pre_state, web, length):
        if length <= 0:
            return (pre_state, ())
        branches = []
        for (post_state, transitions) in web[id(pre_state)][1]:
            branch = self._build_transition_tree(post_state, web, length-1)
            branches.append(branch)
        return (pre_state, tuple(branches))

    def _build_tree_element(self, tree, transition_rules):
        pre_state, branches = tree
        if not branches:
            return None
        alternatives = []
        for branch in branches:
            post_state = branch[0]
            key = (id(pre_state), id(post_state))
            transition_rule = transition_rules[key]
            post_element = self._build_tree_element(branch, transition_rules)
            if post_element:
                branch_element = Sequence((RuleRef(transition_rule),
                                           Optional(post_element)))
            else:
                branch_element = RuleRef(transition_rule)
            alternatives.append(branch_element)
        if len(alternatives) == 1:   element = alternatives[0]
        elif len(alternatives) > 1:  element = Alternative(alternatives)
        else:                        element = None
        return element

    #-----------------------------------------------------------------------

    def load(self, length=3):
        web = self._build_transition_web()
        transition_rules = self._build_transition_rules(web)
        toplevel_rules = self._build_toplevel_rules(web, transition_rules, length)
        self._toplevel_rules = toplevel_rules
        for rule in toplevel_rules:
            self.add_rule(rule)

#        for rule in self.rules:
#            print "loading rule: %r (exported %s)" % (rule.name, rule.exported)
#            print
#            print "    ", rule.gstring()
#            print
#
#        self._log.error("Loading %s" % self)
#        print "loading"
#        import time; time.sleep(2)
        Grammar.load(self)

    def unload(self):
        Grammar.unload(self)
        self._toplevel_rules = ()

    #-----------------------------------------------------------------------

    def process_begin(self, executable, title, handle):
        # Trivial optimization: only check for state-activity changes
        #  if the foreground window has changed in some way.
        details = (executable, title, handle)
        if details == self._previous_details:
            return
        self._previous_details = details

        for rule in self._toplevel_rules:
            if rule.pre_state.is_active_toplevel():
#                print "activating:", rule
                rule.activate()
            else:
#                print "de-activating:", rule
                rule.deactivate()


#===========================================================================

class ToplevelRule(Rule):

    def __init__(self, element, pre_state):
        self._pre_state = pre_state
        name = "_ToplevelRule_%s" % pre_state
        Rule.__init__(self, element=element, name=name, exported=True)

    @property
    def pre_state(self):
        return self._pre_state

    def value(self, node):
        transitions = []
        path = [iter(node.children)]
        while path:
            try:
                head = next(path[-1])
            except StopIteration:
                path.pop()
                continue
            if isinstance(head.actor, TransitionsRule):
#                print "transition words:", head.words()
                transitions.append(head.value())
            else:
                path.append(iter(head.children))
#        print "transitions:", transitions
        return transitions

    def process_recognition(self, node):
#        print "processing recognition:", self
        transitions = self.value(node)
        for transition in transitions:
            transition.execute()


#---------------------------------------------------------------------------

class TransitionsRule(Rule):

    def __init__(self, transitions, pre_state, post_state):
        self._pre_state   = pre_state
        self._post_state  = post_state

        # Build list of alternatives from all transition elements.
        alternatives = [t.command.element for t in transitions]
        if len(alternatives) == 1:  element = alternatives[0]
        else:                       element = Alternative(alternatives)

#        for transition in transitions:
#            print "command element", transition.command.element, id (transition.command.element)

        self._transitions_by_id = dict((id(t.command.element), t)
                                       for t in transitions)

        name = "_TransitionsRule_%s_%s" % (pre_state, post_state)
        Rule.__init__(self, element=element, name=name, exported=False)

    def value(self, node):
        transition_node = node.children[0]
        if id(transition_node.actor) not in self._transitions_by_id:
            transition_node = transition_node.children[0]
#        print "transition node actor", transition_node.actor, id(transition_node.actor)
        transition = self._transitions_by_id[id(transition_node.actor)]
#        print "returning down and transition:", transition_node.words()
        return BoundTransition(transition, transition_node)


#---------------------------------------------------------------------------

class BoundTransition(object):

    def __init__(self, transition, node):
        self._transition = transition
        self._node = node

    def execute(self):
        self._transition.execute(self._node)

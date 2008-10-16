import rule
import elements
import compiler
import core

l = core.GrammarList("somelist")
element = elements.Seq((
	elements.Lit("good morning"),
	elements.Lst(l),
	))
r = rule.Rule("test_rule", element, exported = True)

c = compiler.Compiler()
r.compile(c)
output = c.compile()

print "Compiler state:"
print c.debug_state_string()

print "Output:"
binary = "".join(["%02x" % ord(c) for c in output])
for index in xrange(0, len(binary), 4):
	if index and not index % (8*4): print
	print binary[index: index +4],

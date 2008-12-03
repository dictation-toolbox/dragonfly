
import string
from dragonfly.actions.typeables import typeables
import textwrap

categories = [
    ("Lowercase alphabet", string.lowercase),
    ("Uppercase alphabet", string.uppercase),
    ("Digits", ["%d" % i for i in range(10)]),
    ("Navigation keys", "left right up down pgup pgdown home end".split()),
    ("Editing keys", "space enter backspace del insert".split()),
    ("Symbols", "ampersand apostrophe asterisk at backslash backtick bar caret colon comma dollar dot dquote equal escape exclamation hash hyphen minus percent plus question slash squote tilde underscore".split()),
    ("Function keys", ["f%d" % i for i in range(1, 25)]),
    ("Modifiers", "alt ctrl shift".split()),
    ("Brackets", "langle lbrace lbracket lparen rangle rbrace rbracket rparen".split()),
    ("Special keys", "apps win".split()),
    ("Numberpad keys", "np0 np1 np2 np3 np4 np5 np6 np7 np8 np9 npadd npdec npdiv npmul npsep npsub".split()),
    ]

def format(category, names):
    output = " - %s: %s" % (category,
        ", ".join("``%s``" % name for name in names))
    output = textwrap.wrap(output, width=72, subsequent_indent="   ")
    print "\n".join(output)

collection = []
for category , names in categories:
    for name in names:
        if name not in typeables:
            raise ValueError("Invalid name: %r" % name)

    format(category, names)
    collection.extend(names)

remaining = []
for name, typeable in typeables.iteritems():
    if name not in collection:
        remaining.append(name)

category = "Miscellaneous keys:"
#format(category, remaining)
#remaining.sort(); print "\n".join(remaining)

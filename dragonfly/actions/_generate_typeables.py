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
    This script generates code for in the typeables.py and action_key.py
    files.

"""


(vkey, lookup) = range(2)

key_map = (
    ("Lowercase letter keys", 0, [
        (lookup, "a",                              "a alpha"),
        (lookup, "b",                              "b bravo"),
        (lookup, "c",                              "c charlie"),
        (lookup, "d",                              "d delta"),
        (lookup, "e",                              "e echo"),
        (lookup, "f",                              "f foxtrot"),
        (lookup, "g",                              "g golf"),
        (lookup, "h",                              "h hotel"),
        (lookup, "i",                              "i india"),
        (lookup, "j",                              "j juliet"),
        (lookup, "k",                              "k kilo"),
        (lookup, "l",                              "l lima"),
        (lookup, "m",                              "m mike"),
        (lookup, "n",                              "n november"),
        (lookup, "o",                              "o oscar"),
        (lookup, "p",                              "p papa"),
        (lookup, "q",                              "q quebec"),
        (lookup, "r",                              "r romeo"),
        (lookup, "s",                              "s sierra"),
        (lookup, "t",                              "t tango"),
        (lookup, "u",                              "u uniform"),
        (lookup, "v",                              "v victor"),
        (lookup, "w",                              "w whisky"),
        (lookup, "x",                              "x xray"),
        (lookup, "y",                              "y yankee"),
        (lookup, "z",                              "z zulu")]),
    ("Uppercase letter keys", 0, [
        (lookup, "A",                              "A Alpha"),
        (lookup, "B",                              "B Bravo"),
        (lookup, "C",                              "C Charlie"),
        (lookup, "D",                              "D Delta"),
        (lookup, "E",                              "E Echo"),
        (lookup, "F",                              "F Foxtrot"),
        (lookup, "G",                              "G Golf"),
        (lookup, "H",                              "H Hotel"),
        (lookup, "I",                              "I India"),
        (lookup, "J",                              "J Juliet"),
        (lookup, "K",                              "K Kilo"),
        (lookup, "L",                              "L Lima"),
        (lookup, "M",                              "M Mike"),
        (lookup, "N",                              "N November"),
        (lookup, "O",                              "O Oscar"),
        (lookup, "P",                              "P Papa"),
        (lookup, "Q",                              "Q Quebec"),
        (lookup, "R",                              "R Romeo"),
        (lookup, "S",                              "S Sierra"),
        (lookup, "T",                              "T Tango"),
        (lookup, "U",                              "U Uniform"),
        (lookup, "V",                              "V Victor"),
        (lookup, "W",                              "W Whisky"),
        (lookup, "X",                              "X Xray"),
        (lookup, "Y",                              "Y Yankee"),
        (lookup, "Z",                              "Z Zulu")]),
    ("Number keys", 0, [
        (lookup, "0",                              "0 zero"),
        (lookup, "1",                              "1 one"),
        (lookup, "2",                              "2 two"),
        (lookup, "3",                              "3 three"),
        (lookup, "4",                              "4 four"),
        (lookup, "5",                              "5 five"),
        (lookup, "6",                              "6 six"),
        (lookup, "7",                              "7 seven"),
        (lookup, "8",                              "8 eight"),
        (lookup, "9",                              "9 nine")]),
    ("Symbol keys", 0, [
        (lookup, "!",                              "! bang exclamation"),
        (lookup, "@",                              "@ at"),
        (lookup, "#",                              "# hash"),
        (lookup, "$",                              "$ dollar"),
        (lookup, "%",                              "% percent"),
        (lookup, "^",                              "^ caret"),
        (lookup, "&",                              "& and ampersand"),
        (lookup, "*",                              "* star asterisk"),
        (lookup, "(",                              "( leftparen lparen"),
        (lookup, ")",                              ") rightparen rparen"),
        (lookup, "-",                              "- minus hyphen"),
        (lookup, "_",                              "_ underscore"),
        (lookup, "+",                              "+ plus"),
        (lookup, "`",                              "` backtick"),
        (lookup, "~",                              "~ tilde"),
        (lookup, "[",                              "[ leftbracket lbracket"),
        (lookup, "]",                              "] rightbracket rbracket"),
        (lookup, "{",                              "{ leftbrace lbrace"),
        (lookup, "}",                              "} rightbrace rbrace"),
        (lookup, r"\\",                           r"\\ backslash"),
        (lookup, "|",                              "| bar"),
        (lookup, ":",                              ": colon"),
        (lookup, ";",                              "; semicolon"),
        (lookup, r"\'",                           r"\' apostrophe singlequote squote"),
        (lookup, r'\"',                           r"\" quote doublequote dquote"),
        (lookup, ",",                              ", comma"),
        (lookup, ".",                              ". dot"),
        (lookup, "/",                              "/ slash"),
        (lookup, "<",                              "< lessthan leftangle langle"),
        (lookup, ">",                              "> greaterthan rightangle rangle"),
        (lookup, "?",                              "? question"),
        (lookup, "=",                              "= equal equals")]),
    ("Whitespace and editing keys", 1, [
        (vkey,   "win32con.VK_RETURN",             "enter"),
        (vkey,   "win32con.VK_TAB",                "tab"),
        (vkey,   "win32con.VK_SPACE",              "space"),
        (vkey,   "win32con.VK_BACK",               "backspace"),
        (vkey,   "win32con.VK_DELETE",             "delete del")]),
    ("Main modifier keys", 1, [
        (vkey,   "win32con.VK_SHIFT",              "shift"),
        (vkey,   "win32con.VK_CONTROL",            "control ctrl"),
        (vkey,   "win32con.VK_MENU",               "alt")]),
    ("Right modifier keys", 1, [
        (vkey,   "win32con.VK_RSHIFT",             "rshift"),
        (vkey,   "win32con.VK_RCONTROL",           "rcontrol rctrl"),
        (vkey,   "win32con.VK_RMENU",              "ralt")]),
    ("Special keys", 1, [
        (vkey,   "win32con.VK_ESCAPE",             "escape"),
        (vkey,   "win32con.VK_INSERT",             "insert"),
        (vkey,   "win32con.VK_PAUSE",              "pause"),
        (vkey,   "win32con.VK_LWIN",               "win"),
        (vkey,   "win32con.VK_RWIN",               "rwin"),
        (vkey,   "win32con.VK_APPS",               "apps popup"),
        (vkey,   "win32con.VK_SNAPSHOT",           "snapshot printscreen")]),
    ("Lock keys", 1, [
        (vkey,   "win32con.VK_SCROLL",             "scrolllock"),
        (vkey,   "win32con.VK_NUMLOCK",            "numlock"),
        (vkey,   "win32con.VK_CAPITAL",            "capslock")]),
    ("Navigation keys", 1, [
        (vkey,   "win32con.VK_UP",                 "up"),
        (vkey,   "win32con.VK_DOWN",               "down"),
        (vkey,   "win32con.VK_LEFT",               "left"),
        (vkey,   "win32con.VK_RIGHT",              "right"),
        (vkey,   "win32con.VK_PRIOR",              "pageup pgup"),
        (vkey,   "win32con.VK_NEXT",               "pagedown pgdown"),
        (vkey,   "win32con.VK_HOME",               "home"),
        (vkey,   "win32con.VK_END",                "end")]),
    ("Number pad keys", 1, [
        (vkey,   "win32con.VK_MULTIPLY",           "npmul"),
        (vkey,   "win32con.VK_ADD",                "npadd"),
        (vkey,   "win32con.VK_SEPARATOR",          "npsep"),
        (vkey,   "win32con.VK_SUBTRACT",           "npsub"),
        (vkey,   "win32con.VK_DECIMAL",            "npdec"),
        (vkey,   "win32con.VK_DIVIDE",             "npdiv"),
        (vkey,   "win32con.VK_NUMPAD0",            "numpad0 np0"),
        (vkey,   "win32con.VK_NUMPAD1",            "numpad1 np1"),
        (vkey,   "win32con.VK_NUMPAD2",            "numpad2 np2"),
        (vkey,   "win32con.VK_NUMPAD3",            "numpad3 np3"),
        (vkey,   "win32con.VK_NUMPAD4",            "numpad4 np4"),
        (vkey,   "win32con.VK_NUMPAD5",            "numpad5 np5"),
        (vkey,   "win32con.VK_NUMPAD6",            "numpad6 np6"),
        (vkey,   "win32con.VK_NUMPAD7",            "numpad7 np7"),
        (vkey,   "win32con.VK_NUMPAD8",            "numpad8 np8"),
        (vkey,   "win32con.VK_NUMPAD9",            "numpad9 np9")]),
    ("Function keys", 1, [
        (vkey,   "win32con.VK_F1",                 "f1"),
        (vkey,   "win32con.VK_F2",                 "f2"),
        (vkey,   "win32con.VK_F3",                 "f3"),
        (vkey,   "win32con.VK_F4",                 "f4"),
        (vkey,   "win32con.VK_F5",                 "f5"),
        (vkey,   "win32con.VK_F6",                 "f6"),
        (vkey,   "win32con.VK_F7",                 "f7"),
        (vkey,   "win32con.VK_F8",                 "f8"),
        (vkey,   "win32con.VK_F9",                 "f9"),
        (vkey,   "win32con.VK_F10",                "f10"),
        (vkey,   "win32con.VK_F11",                "f11"),
        (vkey,   "win32con.VK_F12",                "f12"),
        (vkey,   "win32con.VK_F13",                "f13"),
        (vkey,   "win32con.VK_F14",                "f14"),
        (vkey,   "win32con.VK_F15",                "f15"),
        (vkey,   "win32con.VK_F16",                "f16"),
        (vkey,   "win32con.VK_F17",                "f17"),
        (vkey,   "win32con.VK_F18",                "f18"),
        (vkey,   "win32con.VK_F19",                "f19"),
        (vkey,   "win32con.VK_F20",                "f20"),
        (vkey,   "win32con.VK_F21",                "f21"),
        (vkey,   "win32con.VK_F22",                "f22"),
        (vkey,   "win32con.VK_F23",                "f23"),
        (vkey,   "win32con.VK_F24",                "f24")]),
    ("Multimedia keys", 1, [
        (vkey,   "win32con.VK_VOLUME_UP",          "volumeup volup"),
        (vkey,   "win32con.VK_VOLUME_DOWN",        "volumedown voldown"),
        (vkey,   "win32con.VK_VOLUME_MUTE",        "volumemute volmute"),
        (vkey,   "win32con.VK_MEDIA_NEXT_TRACK",   "tracknext"),
        (vkey,   "win32con.VK_MEDIA_PREV_TRACK",   "trackprev"),
        (vkey,   "win32con.VK_MEDIA_PLAY_PAUSE",   "playpause"),
        (vkey,   "win32con.VK_BROWSER_BACK",       "browserback"),
        (vkey,   "win32con.VK_BROWSER_FORWARD",    "browserforward")]),
    )


print("# ---- Code for typeables.py")
for group_name, indent_level, group_map in key_map:
    indent = indent_level * "    "
    print("%s# %s" % (indent , group_name))
    for key_type, key_value, key_names in group_map:
        for key_name in key_names.split():
            if key_type == lookup:
                print('%s_add_typeable(name="%s", char=\'%s\')'
                      % (indent, key_name, key_value))
            elif key_type == vkey:
                value_code = ("Typeable(code=%s, name=%r)"
                              % (key_value, key_name))
                print(('%s"%s": %s%s,'
                       % (indent, key_name, " " * (16-len(key_name)),
                          value_code)))
            else:
                raise Exception("Invalid key type: {0!r} (for {1!r} {2!r})"
                                .format(key_type, key_value, key_names))
    print("")

print("# ---- Code for documentation in action_key.py")
# Exclude reserved characters in the generated documentation.
excluded = "-,:/"
for group_name, _, group_map in key_map:
    parts = [group_name + ":"]
    for key_type, key_value, key_names in group_map:
        key_name_parts = []
        for key_name in key_names.split():
            if key_name not in excluded:
                key_name = key_name.decode("string_escape")
                key_name_parts.append("``" + key_name + "``")
        parts.append(" or ".join(key_name_parts) + ",")
    parts[-1] = parts[-1][:-1]  # Remove trailing comma.
    line = " -"
    for part in parts:
        concatenation = line + " " + part
        if len(concatenation) <= 72:
            line = concatenation
        else:
            print(line)
            line = "   " + part
    print(line)

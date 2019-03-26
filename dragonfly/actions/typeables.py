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
    This file builds the mapping from key-name to Typeable instances.

    To make changes/additions to the mappings, use the _generate_typeables.py
    script to generate the list and copy-paste the relevant section into
    this file.

    The script also generates documentation for the :class:`Key` action.

"""

import logging
import sys
from dragonfly.actions.keyboard import keyboard, Typeable

logging.basicConfig()
_log = logging.getLogger("actions.typeables")


# --------------------------------------------------------------------------
# Mapping of name -> typeable.

typeables = {}


def _add_typeable(name, char):
    # Add a character to the typeables dictionary if it is typeable with
    # the current keyboard layout or log an error if it isn't.
    try:
        typeables[name] = keyboard.get_typeable(char)
    except ValueError as e:
        _log.error(e)


# Lowercase letter keys
_add_typeable(name="a", char='a')
_add_typeable(name="alpha", char='a')
_add_typeable(name="b", char='b')
_add_typeable(name="bravo", char='b')
_add_typeable(name="c", char='c')
_add_typeable(name="charlie", char='c')
_add_typeable(name="d", char='d')
_add_typeable(name="delta", char='d')
_add_typeable(name="e", char='e')
_add_typeable(name="echo", char='e')
_add_typeable(name="f", char='f')
_add_typeable(name="foxtrot", char='f')
_add_typeable(name="g", char='g')
_add_typeable(name="golf", char='g')
_add_typeable(name="h", char='h')
_add_typeable(name="hotel", char='h')
_add_typeable(name="i", char='i')
_add_typeable(name="india", char='i')
_add_typeable(name="j", char='j')
_add_typeable(name="juliet", char='j')
_add_typeable(name="k", char='k')
_add_typeable(name="kilo", char='k')
_add_typeable(name="l", char='l')
_add_typeable(name="lima", char='l')
_add_typeable(name="m", char='m')
_add_typeable(name="mike", char='m')
_add_typeable(name="n", char='n')
_add_typeable(name="november", char='n')
_add_typeable(name="o", char='o')
_add_typeable(name="oscar", char='o')
_add_typeable(name="p", char='p')
_add_typeable(name="papa", char='p')
_add_typeable(name="q", char='q')
_add_typeable(name="quebec", char='q')
_add_typeable(name="r", char='r')
_add_typeable(name="romeo", char='r')
_add_typeable(name="s", char='s')
_add_typeable(name="sierra", char='s')
_add_typeable(name="t", char='t')
_add_typeable(name="tango", char='t')
_add_typeable(name="u", char='u')
_add_typeable(name="uniform", char='u')
_add_typeable(name="v", char='v')
_add_typeable(name="victor", char='v')
_add_typeable(name="w", char='w')
_add_typeable(name="whisky", char='w')
_add_typeable(name="x", char='x')
_add_typeable(name="xray", char='x')
_add_typeable(name="y", char='y')
_add_typeable(name="yankee", char='y')
_add_typeable(name="z", char='z')
_add_typeable(name="zulu", char='z')

# Uppercase letter keys
_add_typeable(name="A", char='A')
_add_typeable(name="Alpha", char='A')
_add_typeable(name="B", char='B')
_add_typeable(name="Bravo", char='B')
_add_typeable(name="C", char='C')
_add_typeable(name="Charlie", char='C')
_add_typeable(name="D", char='D')
_add_typeable(name="Delta", char='D')
_add_typeable(name="E", char='E')
_add_typeable(name="Echo", char='E')
_add_typeable(name="F", char='F')
_add_typeable(name="Foxtrot", char='F')
_add_typeable(name="G", char='G')
_add_typeable(name="Golf", char='G')
_add_typeable(name="H", char='H')
_add_typeable(name="Hotel", char='H')
_add_typeable(name="I", char='I')
_add_typeable(name="India", char='I')
_add_typeable(name="J", char='J')
_add_typeable(name="Juliet", char='J')
_add_typeable(name="K", char='K')
_add_typeable(name="Kilo", char='K')
_add_typeable(name="L", char='L')
_add_typeable(name="Lima", char='L')
_add_typeable(name="M", char='M')
_add_typeable(name="Mike", char='M')
_add_typeable(name="N", char='N')
_add_typeable(name="November", char='N')
_add_typeable(name="O", char='O')
_add_typeable(name="Oscar", char='O')
_add_typeable(name="P", char='P')
_add_typeable(name="Papa", char='P')
_add_typeable(name="Q", char='Q')
_add_typeable(name="Quebec", char='Q')
_add_typeable(name="R", char='R')
_add_typeable(name="Romeo", char='R')
_add_typeable(name="S", char='S')
_add_typeable(name="Sierra", char='S')
_add_typeable(name="T", char='T')
_add_typeable(name="Tango", char='T')
_add_typeable(name="U", char='U')
_add_typeable(name="Uniform", char='U')
_add_typeable(name="V", char='V')
_add_typeable(name="Victor", char='V')
_add_typeable(name="W", char='W')
_add_typeable(name="Whisky", char='W')
_add_typeable(name="X", char='X')
_add_typeable(name="Xray", char='X')
_add_typeable(name="Y", char='Y')
_add_typeable(name="Yankee", char='Y')
_add_typeable(name="Z", char='Z')
_add_typeable(name="Zulu", char='Z')

# Number keys
_add_typeable(name="0", char='0')
_add_typeable(name="zero", char='0')
_add_typeable(name="1", char='1')
_add_typeable(name="one", char='1')
_add_typeable(name="2", char='2')
_add_typeable(name="two", char='2')
_add_typeable(name="3", char='3')
_add_typeable(name="three", char='3')
_add_typeable(name="4", char='4')
_add_typeable(name="four", char='4')
_add_typeable(name="5", char='5')
_add_typeable(name="five", char='5')
_add_typeable(name="6", char='6')
_add_typeable(name="six", char='6')
_add_typeable(name="7", char='7')
_add_typeable(name="seven", char='7')
_add_typeable(name="8", char='8')
_add_typeable(name="eight", char='8')
_add_typeable(name="9", char='9')
_add_typeable(name="nine", char='9')

# Symbol keys
# All symbols can be referred to by their printable representation.
# Reserved characters for the Key action spec -,:/ are still typeables,
# but Key requires use of the longer character names.
_add_typeable(name="!", char='!')
_add_typeable(name="bang", char='!')
_add_typeable(name="exclamation", char='!')
_add_typeable(name="@", char='@')
_add_typeable(name="at", char='@')
_add_typeable(name="#", char='#')
_add_typeable(name="hash", char='#')
_add_typeable(name="$", char='$')
_add_typeable(name="dollar", char='$')
_add_typeable(name="%", char='%')
_add_typeable(name="percent", char='%')
_add_typeable(name="^", char='^')
_add_typeable(name="caret", char='^')
_add_typeable(name="&", char='&')
_add_typeable(name="and", char='&')
_add_typeable(name="ampersand", char='&')
_add_typeable(name="*", char='*')
_add_typeable(name="star", char='*')
_add_typeable(name="asterisk", char='*')
_add_typeable(name="(", char='(')
_add_typeable(name="leftparen", char='(')
_add_typeable(name="lparen", char='(')
_add_typeable(name=")", char=')')
_add_typeable(name="rightparen", char=')')
_add_typeable(name="rparen", char=')')
_add_typeable(name="-", char='-')
_add_typeable(name="minus", char='-')
_add_typeable(name="hyphen", char='-')
_add_typeable(name="_", char='_')
_add_typeable(name="underscore", char='_')
_add_typeable(name="+", char='+')
_add_typeable(name="plus", char='+')
_add_typeable(name="`", char='`')
_add_typeable(name="backtick", char='`')
_add_typeable(name="~", char='~')
_add_typeable(name="tilde", char='~')
_add_typeable(name="[", char='[')
_add_typeable(name="leftbracket", char='[')
_add_typeable(name="lbracket", char='[')
_add_typeable(name="]", char=']')
_add_typeable(name="rightbracket", char=']')
_add_typeable(name="rbracket", char=']')
_add_typeable(name="{", char='{')
_add_typeable(name="leftbrace", char='{')
_add_typeable(name="lbrace", char='{')
_add_typeable(name="}", char='}')
_add_typeable(name="rightbrace", char='}')
_add_typeable(name="rbrace", char='}')
_add_typeable(name="\\", char='\\')
_add_typeable(name="backslash", char='\\')
_add_typeable(name="|", char='|')
_add_typeable(name="bar", char='|')
_add_typeable(name=":", char=':')
_add_typeable(name="colon", char=':')
_add_typeable(name=";", char=';')
_add_typeable(name="semicolon", char=';')
_add_typeable(name="\'", char='\'')
_add_typeable(name="apostrophe", char='\'')
_add_typeable(name="singlequote", char='\'')
_add_typeable(name="squote", char='\'')
_add_typeable(name="\"", char='\"')
_add_typeable(name="quote", char='\"')
_add_typeable(name="doublequote", char='\"')
_add_typeable(name="dquote", char='\"')
_add_typeable(name=",", char=',')
_add_typeable(name="comma", char=',')
_add_typeable(name=".", char='.')
_add_typeable(name="dot", char='.')
_add_typeable(name="/", char='/')
_add_typeable(name="slash", char='/')
_add_typeable(name="<", char='<')
_add_typeable(name="lessthan", char='<')
_add_typeable(name="leftangle", char='<')
_add_typeable(name="langle", char='<')
_add_typeable(name=">", char='>')
_add_typeable(name="greaterthan", char='>')
_add_typeable(name="rightangle", char='>')
_add_typeable(name="rangle", char='>')
_add_typeable(name="?", char='?')
_add_typeable(name="question", char='?')
_add_typeable(name="=", char='=')
_add_typeable(name="equal", char='=')
_add_typeable(name="equals", char='=')

typeables.update({
    # Symbol keys
    "bang":             keyboard.get_typeable(char='!'),
    "exclamation":      keyboard.get_typeable(char='!'),
    "at":               keyboard.get_typeable(char='@'),
    "hash":             keyboard.get_typeable(char='#'),
    "dollar":           keyboard.get_typeable(char='$'),
    "percent":          keyboard.get_typeable(char='%'),
    "caret":            keyboard.get_typeable(char='^'),
    "and":              keyboard.get_typeable(char='&'),
    "ampersand":        keyboard.get_typeable(char='&'),
    "star":             keyboard.get_typeable(char='*'),
    "asterisk":         keyboard.get_typeable(char='*'),
    "leftparen":        keyboard.get_typeable(char='('),
    "lparen":           keyboard.get_typeable(char='('),
    "rightparen":       keyboard.get_typeable(char=')'),
    "rparen":           keyboard.get_typeable(char=')'),
    "minus":            keyboard.get_typeable(char='-'),
    "hyphen":           keyboard.get_typeable(char='-'),
    "underscore":       keyboard.get_typeable(char='_'),
    "plus":             keyboard.get_typeable(char='+'),
    "backtick":         keyboard.get_typeable(char='`'),
    "tilde":            keyboard.get_typeable(char='~'),
    "leftbracket":      keyboard.get_typeable(char='['),
    "lbracket":         keyboard.get_typeable(char='['),
    "rightbracket":     keyboard.get_typeable(char=']'),
    "rbracket":         keyboard.get_typeable(char=']'),
    "leftbrace":        keyboard.get_typeable(char='{'),
    "lbrace":           keyboard.get_typeable(char='{'),
    "rightbrace":       keyboard.get_typeable(char='}'),
    "rbrace":           keyboard.get_typeable(char='}'),
    "backslash":        keyboard.get_typeable(char='\\'),
    "bar":              keyboard.get_typeable(char='|'),
    "colon":            keyboard.get_typeable(char=':'),
    "semicolon":        keyboard.get_typeable(char=';'),
    "apostrophe":       keyboard.get_typeable(char="'"),
    "singlequote":      keyboard.get_typeable(char="'"),
    "squote":           keyboard.get_typeable(char="'"),
    "quote":            keyboard.get_typeable(char='"'),
    "doublequote":      keyboard.get_typeable(char='"'),
    "dquote":           keyboard.get_typeable(char='"'),
    "comma":            keyboard.get_typeable(char=','),
    "dot":              keyboard.get_typeable(char='.'),
    "slash":            keyboard.get_typeable(char='/'),
    "lessthan":         keyboard.get_typeable(char='<'),
    "leftangle":        keyboard.get_typeable(char='<'),
    "langle":           keyboard.get_typeable(char='<'),
    "greaterthan":      keyboard.get_typeable(char='>'),
    "rightangle":       keyboard.get_typeable(char='>'),
    "rangle":           keyboard.get_typeable(char='>'),
    "question":         keyboard.get_typeable(char='?'),
    "equal":            keyboard.get_typeable(char='='),
    "equals":           keyboard.get_typeable(char='='),
})

if sys.platform.startswith("win"):
    import win32con
    win_typeables = {
    # Whitespace and editing keys
    "enter":            Typeable(code=win32con.VK_RETURN, name='enter'),
    "tab":              Typeable(code=win32con.VK_TAB, name='tab'),
    "space":            Typeable(code=win32con.VK_SPACE, name='space'),
    "backspace":        Typeable(code=win32con.VK_BACK, name='backspace'),
    "delete":           Typeable(code=win32con.VK_DELETE, name='delete'),
    "del":              Typeable(code=win32con.VK_DELETE, name='del'),

    # Main modifier keys
    "shift":            Typeable(code=win32con.VK_SHIFT, name='shift'),
    "control":          Typeable(code=win32con.VK_CONTROL, name='control'),
    "ctrl":             Typeable(code=win32con.VK_CONTROL, name='ctrl'),
    "alt":              Typeable(code=win32con.VK_MENU, name='alt'),

    # Right modifier keys
    "rshift":           Typeable(code=win32con.VK_RSHIFT, name='rshift'),
    "rcontrol":         Typeable(code=win32con.VK_RCONTROL, name='rcontrol'),
    "rctrl":            Typeable(code=win32con.VK_RCONTROL, name='rctrl'),
    "ralt":             Typeable(code=win32con.VK_RMENU, name='ralt'),

    # Special keys
    "escape":           Typeable(code=win32con.VK_ESCAPE, name='escape'),
    "insert":           Typeable(code=win32con.VK_INSERT, name='insert'),
    "pause":            Typeable(code=win32con.VK_PAUSE, name='pause'),
    "win":              Typeable(code=win32con.VK_LWIN, name='win'),
    "rwin":             Typeable(code=win32con.VK_RWIN, name='rwin'),
    "apps":             Typeable(code=win32con.VK_APPS, name='apps'),
    "popup":            Typeable(code=win32con.VK_APPS, name='popup'),
    "snapshot":         Typeable(code=win32con.VK_SNAPSHOT, name='snapshot'),
    "printscreen":      Typeable(code=win32con.VK_SNAPSHOT, name='printscreen'),

    # Lock keys
    # win32api.GetKeyState(code) could be used to toggle lock keys sensibly
    # instead of using the up/down modifiers.
    "scrolllock":       Typeable(code=win32con.VK_SCROLL, name='scrolllock'),
    "numlock":          Typeable(code=win32con.VK_NUMLOCK, name='numlock'),
    "capslock":         Typeable(code=win32con.VK_CAPITAL, name='capslock'),

    # Navigation keys
    "up":               Typeable(code=win32con.VK_UP, name='up'),
    "down":             Typeable(code=win32con.VK_DOWN, name='down'),
    "left":             Typeable(code=win32con.VK_LEFT, name='left'),
    "right":            Typeable(code=win32con.VK_RIGHT, name='right'),
    "pageup":           Typeable(code=win32con.VK_PRIOR, name='pageup'),
    "pgup":             Typeable(code=win32con.VK_PRIOR, name='pgup'),
    "pagedown":         Typeable(code=win32con.VK_NEXT, name='pagedown'),
    "pgdown":           Typeable(code=win32con.VK_NEXT, name='pgdown'),
    "home":             Typeable(code=win32con.VK_HOME, name='home'),
    "end":              Typeable(code=win32con.VK_END, name='end'),

    # Number pad keys
    "npmul":            Typeable(code=win32con.VK_MULTIPLY, name='npmul'),
    "npadd":            Typeable(code=win32con.VK_ADD, name='npadd'),
    "npsep":            Typeable(code=win32con.VK_SEPARATOR, name='npsep'),
    "npsub":            Typeable(code=win32con.VK_SUBTRACT, name='npsub'),
    "npdec":            Typeable(code=win32con.VK_DECIMAL, name='npdec'),
    "npdiv":            Typeable(code=win32con.VK_DIVIDE, name='npdiv'),
    "numpad0":          Typeable(code=win32con.VK_NUMPAD0, name='numpad0'),
    "np0":              Typeable(code=win32con.VK_NUMPAD0, name='np0'),
    "numpad1":          Typeable(code=win32con.VK_NUMPAD1, name='numpad1'),
    "np1":              Typeable(code=win32con.VK_NUMPAD1, name='np1'),
    "numpad2":          Typeable(code=win32con.VK_NUMPAD2, name='numpad2'),
    "np2":              Typeable(code=win32con.VK_NUMPAD2, name='np2'),
    "numpad3":          Typeable(code=win32con.VK_NUMPAD3, name='numpad3'),
    "np3":              Typeable(code=win32con.VK_NUMPAD3, name='np3'),
    "numpad4":          Typeable(code=win32con.VK_NUMPAD4, name='numpad4'),
    "np4":              Typeable(code=win32con.VK_NUMPAD4, name='np4'),
    "numpad5":          Typeable(code=win32con.VK_NUMPAD5, name='numpad5'),
    "np5":              Typeable(code=win32con.VK_NUMPAD5, name='np5'),
    "numpad6":          Typeable(code=win32con.VK_NUMPAD6, name='numpad6'),
    "np6":              Typeable(code=win32con.VK_NUMPAD6, name='np6'),
    "numpad7":          Typeable(code=win32con.VK_NUMPAD7, name='numpad7'),
    "np7":              Typeable(code=win32con.VK_NUMPAD7, name='np7'),
    "numpad8":          Typeable(code=win32con.VK_NUMPAD8, name='numpad8'),
    "np8":              Typeable(code=win32con.VK_NUMPAD8, name='np8'),
    "numpad9":          Typeable(code=win32con.VK_NUMPAD9, name='numpad9'),
    "np9":              Typeable(code=win32con.VK_NUMPAD9, name='np9'),

    # Function keys
    "f1":               Typeable(code=win32con.VK_F1, name='f1'),
    "f2":               Typeable(code=win32con.VK_F2, name='f2'),
    "f3":               Typeable(code=win32con.VK_F3, name='f3'),
    "f4":               Typeable(code=win32con.VK_F4, name='f4'),
    "f5":               Typeable(code=win32con.VK_F5, name='f5'),
    "f6":               Typeable(code=win32con.VK_F6, name='f6'),
    "f7":               Typeable(code=win32con.VK_F7, name='f7'),
    "f8":               Typeable(code=win32con.VK_F8, name='f8'),
    "f9":               Typeable(code=win32con.VK_F9, name='f9'),
    "f10":              Typeable(code=win32con.VK_F10, name='f10'),
    "f11":              Typeable(code=win32con.VK_F11, name='f11'),
    "f12":              Typeable(code=win32con.VK_F12, name='f12'),
    "f13":              Typeable(code=win32con.VK_F13, name='f13'),
    "f14":              Typeable(code=win32con.VK_F14, name='f14'),
    "f15":              Typeable(code=win32con.VK_F15, name='f15'),
    "f16":              Typeable(code=win32con.VK_F16, name='f16'),
    "f17":              Typeable(code=win32con.VK_F17, name='f17'),
    "f18":              Typeable(code=win32con.VK_F18, name='f18'),
    "f19":              Typeable(code=win32con.VK_F19, name='f19'),
    "f20":              Typeable(code=win32con.VK_F20, name='f20'),
    "f21":              Typeable(code=win32con.VK_F21, name='f21'),
    "f22":              Typeable(code=win32con.VK_F22, name='f22'),
    "f23":              Typeable(code=win32con.VK_F23, name='f23'),
    "f24":              Typeable(code=win32con.VK_F24, name='f24'),

    # Multimedia keys
    "volumeup":         Typeable(code=win32con.VK_VOLUME_UP, name='volumeup'),
    "volup":            Typeable(code=win32con.VK_VOLUME_UP, name='volup'),
    "volumedown":       Typeable(code=win32con.VK_VOLUME_DOWN, name='volumedown'),
    "voldown":          Typeable(code=win32con.VK_VOLUME_DOWN, name='voldown'),
    "volumemute":       Typeable(code=win32con.VK_VOLUME_MUTE, name='volumemute'),
    "volmute":          Typeable(code=win32con.VK_VOLUME_MUTE, name='volmute'),
    "tracknext":        Typeable(code=win32con.VK_MEDIA_NEXT_TRACK, name='tracknext'),
    "trackprev":        Typeable(code=win32con.VK_MEDIA_PREV_TRACK, name='trackprev'),
    "playpause":        Typeable(code=win32con.VK_MEDIA_PLAY_PAUSE, name='playpause'),
    "browserback":      Typeable(code=win32con.VK_BROWSER_BACK, name='browserback'),
    "browserforward":   Typeable(code=win32con.VK_BROWSER_FORWARD, name='browserforward'),
    }
    typeables.update(win_typeables)
elif sys.platform.startswith("linux"):
    other_typeables = {
    # Whitespace and editing keys
    "enter":            keyboard.get_named_typeable(name='enter'),
    "tab":              keyboard.get_named_typeable(name='tab'),
    "space":            keyboard.get_named_typeable(name='space'),
    "backspace":        keyboard.get_named_typeable(name='backspace'),
    "delete":           keyboard.get_named_typeable(name='delete'),
    "del":              keyboard.get_named_typeable(name='del'),

    # Main modifier keys
    "shift":            keyboard.get_named_typeable(name='shift'),
    "control":          keyboard.get_named_typeable(name='control'),
    "ctrl":             keyboard.get_named_typeable(name='ctrl'),
    "alt":              keyboard.get_named_typeable(name='alt'),

    # Right modifier keys
    "ralt":             keyboard.get_named_typeable(name='ralt'),
    "rshift":           keyboard.get_named_typeable(name='rshift'),
    "rcontrol":         keyboard.get_named_typeable(name='rcontrol'),
    "rctrl":            keyboard.get_named_typeable(name='rctrl'),

    # Special keys
    "escape":           keyboard.get_named_typeable(name='escape'),
    "insert":           keyboard.get_named_typeable(name='insert'),
    "pause":            keyboard.get_named_typeable(name='pause'),
    "win":              keyboard.get_named_typeable(name='win'),
    "rwin":             keyboard.get_named_typeable(name='rwin'),
    "apps":             keyboard.get_named_typeable(name='apps'),
    "popup":            keyboard.get_named_typeable(name='popup'),
    "snapshot":         keyboard.get_named_typeable(name='snapshot'),
    "printscreen":      keyboard.get_named_typeable(name='printscreen'),

    # Lock keys
    # win32api.GetKeyState(code) could be used to toggle lock keys sensibly
    # instead of using the up/down modifiers.
    "scrolllock":       keyboard.get_named_typeable(name='scrolllock'),
    "numlock":          keyboard.get_named_typeable(name='numlock'),
    "capslock":         keyboard.get_named_typeable(name='capslock'),

    # Navigation keys
    "up":               keyboard.get_named_typeable(name='up'),
    "down":             keyboard.get_named_typeable(name='down'),
    "left":             keyboard.get_named_typeable(name='left'),
    "right":            keyboard.get_named_typeable(name='right'),
    "pageup":           keyboard.get_named_typeable(name='pageup'),
    "pgup":             keyboard.get_named_typeable(name='pgup'),
    "pagedown":         keyboard.get_named_typeable(name='pagedown'),
    "pgdown":           keyboard.get_named_typeable(name='pgdown'),
    "home":             keyboard.get_named_typeable(name='home'),
    "end":              keyboard.get_named_typeable(name='end'),

    # Number pad keys
    "npmul":            keyboard.get_named_typeable(name='npmul'),
    "npadd":            keyboard.get_named_typeable(name='npadd'),
    "npsep":            keyboard.get_named_typeable(name='npsep'),
    "npsub":            keyboard.get_named_typeable(name='npsub'),
    "npdec":            keyboard.get_named_typeable(name='npdec'),
    "npdiv":            keyboard.get_named_typeable(name='npdiv'),
    "numpad0":          keyboard.get_named_typeable(name='numpad0'),
    "np0":              keyboard.get_named_typeable(name='np0'),
    "numpad1":          keyboard.get_named_typeable(name='numpad1'),
    "np1":              keyboard.get_named_typeable(name='np1'),
    "numpad2":          keyboard.get_named_typeable(name='numpad2'),
    "np2":              keyboard.get_named_typeable(name='np2'),
    "numpad3":          keyboard.get_named_typeable(name='numpad3'),
    "np3":              keyboard.get_named_typeable(name='np3'),
    "numpad4":          keyboard.get_named_typeable(name='numpad4'),
    "np4":              keyboard.get_named_typeable(name='np4'),
    "numpad5":          keyboard.get_named_typeable(name='numpad5'),
    "np5":              keyboard.get_named_typeable(name='np5'),
    "numpad6":          keyboard.get_named_typeable(name='numpad6'),
    "np6":              keyboard.get_named_typeable(name='np6'),
    "numpad7":          keyboard.get_named_typeable(name='numpad7'),
    "np7":              keyboard.get_named_typeable(name='np7'),
    "numpad8":          keyboard.get_named_typeable(name='numpad8'),
    "np8":              keyboard.get_named_typeable(name='np8'),
    "numpad9":          keyboard.get_named_typeable(name='numpad9'),
    "np9":              keyboard.get_named_typeable(name='np9'),

    # Function keys
    "f1":               keyboard.get_named_typeable(name='f1'),
    "f2":               keyboard.get_named_typeable(name='f2'),
    "f3":               keyboard.get_named_typeable(name='f3'),
    "f4":               keyboard.get_named_typeable(name='f4'),
    "f5":               keyboard.get_named_typeable(name='f5'),
    "f6":               keyboard.get_named_typeable(name='f6'),
    "f7":               keyboard.get_named_typeable(name='f7'),
    "f8":               keyboard.get_named_typeable(name='f8'),
    "f9":               keyboard.get_named_typeable(name='f9'),
    "f10":              keyboard.get_named_typeable(name='f10'),
    "f11":              keyboard.get_named_typeable(name='f11'),
    "f12":              keyboard.get_named_typeable(name='f12'),
    "f13":              keyboard.get_named_typeable(name='f13'),
    "f14":              keyboard.get_named_typeable(name='f14'),
    "f15":              keyboard.get_named_typeable(name='f15'),
    "f16":              keyboard.get_named_typeable(name='f16'),
    "f17":              keyboard.get_named_typeable(name='f17'),
    "f18":              keyboard.get_named_typeable(name='f18'),
    "f19":              keyboard.get_named_typeable(name='f19'),
    "f20":              keyboard.get_named_typeable(name='f20'),
    "f21":              keyboard.get_named_typeable(name='f21'),
    "f22":              keyboard.get_named_typeable(name='f22'),
    "f23":              keyboard.get_named_typeable(name='f23'),
    "f24":              keyboard.get_named_typeable(name='f24'),

    # Multimedia keys
    "volumeup":         keyboard.get_named_typeable(name='volumeup'),
    "volup":            keyboard.get_named_typeable(name='volup'),
    "volumedown":       keyboard.get_named_typeable(name='volumedown'),
    "voldown":          keyboard.get_named_typeable(name='voldown'),
    "volumemute":       keyboard.get_named_typeable(name='volumemute'),
    "volmute":          keyboard.get_named_typeable(name='volmute'),
    "tracknext":        keyboard.get_named_typeable(name='tracknext'),
    "trackprev":        keyboard.get_named_typeable(name='trackprev'),
    "playpause":        keyboard.get_named_typeable(name='playpause'),
    "browserback":      keyboard.get_named_typeable(name='browserback'),
    "browserforward":   keyboard.get_named_typeable(name='browserforward'),
    }
    typeables.update(other_typeables)

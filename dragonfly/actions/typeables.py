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

from .keyboard import keyboard, Typeable, KeySymbols


# --------------------------------------------------------------------------
# Mapping of name -> typeable.

typeables = {}
key_symbols = KeySymbols()


def _add_typeable(name, char):
    # Add a character to the typeables dictionary if it is typeable with
    # the current keyboard layout.
    try:
        typeables[name] = keyboard.get_typeable(char)
    except ValueError:
        # Errors or log messages will occur later if code attempts to use
        # missing typeables.
        pass


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
# Reserved characters for the Key action spec -,:/ are Typeable objects,
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
    # Whitespace and editing keys
    "enter":            Typeable(code=key_symbols.RETURN, name='enter'),
    "tab":              Typeable(code=key_symbols.TAB, name='tab'),
    "space":            Typeable(code=key_symbols.SPACE, name='space'),
    "backspace":        Typeable(code=key_symbols.BACK, name='backspace'),
    "delete":           Typeable(code=key_symbols.DELETE, name='delete'),
    "del":              Typeable(code=key_symbols.DELETE, name='del'),

    # Main modifier keys
    "shift":            Typeable(code=key_symbols.SHIFT, name='shift'),
    "control":          Typeable(code=key_symbols.CONTROL, name='control'),
    "ctrl":             Typeable(code=key_symbols.CONTROL, name='ctrl'),
    "alt":              Typeable(code=key_symbols.ALT, name='alt'),

    # Right modifier keys
    "rshift":           Typeable(code=key_symbols.RSHIFT, name='rshift'),
    "rcontrol":         Typeable(code=key_symbols.RCONTROL, name='rcontrol'),
    "rctrl":            Typeable(code=key_symbols.RCONTROL, name='rctrl'),
    "ralt":             Typeable(code=key_symbols.RALT, name='ralt'),

    # Special keys
    "escape":           Typeable(code=key_symbols.ESCAPE, name='escape'),
    "insert":           Typeable(code=key_symbols.INSERT, name='insert'),
    "pause":            Typeable(code=key_symbols.PAUSE, name='pause'),
    "win":              Typeable(code=key_symbols.LSUPER, name='win'),
    "rwin":             Typeable(code=key_symbols.RSUPER, name='rwin'),
    "apps":             Typeable(code=key_symbols.APPS, name='apps'),
    "popup":            Typeable(code=key_symbols.APPS, name='popup'),
    "snapshot":         Typeable(code=key_symbols.SNAPSHOT, name='snapshot'),
    "printscreen":      Typeable(code=key_symbols.SNAPSHOT, name='printscreen'),

    # Lock keys
    # win32api.GetKeyState(code) could be used to toggle lock keys sensibly
    # instead of using the up/down modifiers.
    "scrolllock":       Typeable(code=key_symbols.SCROLL_LOCK, name='scrolllock'),
    "numlock":          Typeable(code=key_symbols.NUM_LOCK, name='numlock'),
    "capslock":         Typeable(code=key_symbols.CAPS_LOCK, name='capslock'),

    # Navigation keys
    "up":               Typeable(code=key_symbols.UP, name='up'),
    "down":             Typeable(code=key_symbols.DOWN, name='down'),
    "left":             Typeable(code=key_symbols.LEFT, name='left'),
    "right":            Typeable(code=key_symbols.RIGHT, name='right'),
    "pageup":           Typeable(code=key_symbols.PAGE_UP, name='pageup'),
    "pgup":             Typeable(code=key_symbols.PAGE_UP, name='pgup'),
    "pagedown":         Typeable(code=key_symbols.PAGE_DOWN, name='pagedown'),
    "pgdown":           Typeable(code=key_symbols.PAGE_DOWN, name='pgdown'),
    "home":             Typeable(code=key_symbols.HOME, name='home'),
    "end":              Typeable(code=key_symbols.END, name='end'),

    # Number pad keys
    "npmul":            Typeable(code=key_symbols.MULTIPLY, name='npmul'),
    "npadd":            Typeable(code=key_symbols.ADD, name='npadd'),
    "npsep":            Typeable(code=key_symbols.SEPARATOR, name='npsep'),
    "npsub":            Typeable(code=key_symbols.SUBTRACT, name='npsub'),
    "npdec":            Typeable(code=key_symbols.DECIMAL, name='npdec'),
    "npdiv":            Typeable(code=key_symbols.DIVIDE, name='npdiv'),
    "numpad0":          Typeable(code=key_symbols.NUMPAD0, name='numpad0'),
    "np0":              Typeable(code=key_symbols.NUMPAD0, name='np0'),
    "numpad1":          Typeable(code=key_symbols.NUMPAD1, name='numpad1'),
    "np1":              Typeable(code=key_symbols.NUMPAD1, name='np1'),
    "numpad2":          Typeable(code=key_symbols.NUMPAD2, name='numpad2'),
    "np2":              Typeable(code=key_symbols.NUMPAD2, name='np2'),
    "numpad3":          Typeable(code=key_symbols.NUMPAD3, name='numpad3'),
    "np3":              Typeable(code=key_symbols.NUMPAD3, name='np3'),
    "numpad4":          Typeable(code=key_symbols.NUMPAD4, name='numpad4'),
    "np4":              Typeable(code=key_symbols.NUMPAD4, name='np4'),
    "numpad5":          Typeable(code=key_symbols.NUMPAD5, name='numpad5'),
    "np5":              Typeable(code=key_symbols.NUMPAD5, name='np5'),
    "numpad6":          Typeable(code=key_symbols.NUMPAD6, name='numpad6'),
    "np6":              Typeable(code=key_symbols.NUMPAD6, name='np6'),
    "numpad7":          Typeable(code=key_symbols.NUMPAD7, name='numpad7'),
    "np7":              Typeable(code=key_symbols.NUMPAD7, name='np7'),
    "numpad8":          Typeable(code=key_symbols.NUMPAD8, name='numpad8'),
    "np8":              Typeable(code=key_symbols.NUMPAD8, name='np8'),
    "numpad9":          Typeable(code=key_symbols.NUMPAD9, name='numpad9'),
    "np9":              Typeable(code=key_symbols.NUMPAD9, name='np9'),

    # Function keys
    "f1":               Typeable(code=key_symbols.F1, name='f1'),
    "f2":               Typeable(code=key_symbols.F2, name='f2'),
    "f3":               Typeable(code=key_symbols.F3, name='f3'),
    "f4":               Typeable(code=key_symbols.F4, name='f4'),
    "f5":               Typeable(code=key_symbols.F5, name='f5'),
    "f6":               Typeable(code=key_symbols.F6, name='f6'),
    "f7":               Typeable(code=key_symbols.F7, name='f7'),
    "f8":               Typeable(code=key_symbols.F8, name='f8'),
    "f9":               Typeable(code=key_symbols.F9, name='f9'),
    "f10":              Typeable(code=key_symbols.F10, name='f10'),
    "f11":              Typeable(code=key_symbols.F11, name='f11'),
    "f12":              Typeable(code=key_symbols.F12, name='f12'),
    "f13":              Typeable(code=key_symbols.F13, name='f13'),
    "f14":              Typeable(code=key_symbols.F14, name='f14'),
    "f15":              Typeable(code=key_symbols.F15, name='f15'),
    "f16":              Typeable(code=key_symbols.F16, name='f16'),
    "f17":              Typeable(code=key_symbols.F17, name='f17'),
    "f18":              Typeable(code=key_symbols.F18, name='f18'),
    "f19":              Typeable(code=key_symbols.F19, name='f19'),
    "f20":              Typeable(code=key_symbols.F20, name='f20'),
    "f21":              Typeable(code=key_symbols.F21, name='f21'),
    "f22":              Typeable(code=key_symbols.F22, name='f22'),
    "f23":              Typeable(code=key_symbols.F23, name='f23'),
    "f24":              Typeable(code=key_symbols.F24, name='f24'),

    # Multimedia keys
    "volumeup":         Typeable(code=key_symbols.VOLUME_UP, name='volumeup'),
    "volup":            Typeable(code=key_symbols.VOLUME_UP, name='volup'),
    "volumedown":       Typeable(code=key_symbols.VOLUME_DOWN, name='volumedown'),
    "voldown":          Typeable(code=key_symbols.VOLUME_DOWN, name='voldown'),
    "volumemute":       Typeable(code=key_symbols.VOLUME_MUTE, name='volumemute'),
    "volmute":          Typeable(code=key_symbols.VOLUME_MUTE, name='volmute'),
    "tracknext":        Typeable(code=key_symbols.MEDIA_NEXT_TRACK, name='tracknext'),
    "trackprev":        Typeable(code=key_symbols.MEDIA_PREV_TRACK, name='trackprev'),
    "playpause":        Typeable(code=key_symbols.MEDIA_PLAY_PAUSE, name='playpause'),
    "browserback":      Typeable(code=key_symbols.BROWSER_BACK, name='browserback'),
    "browserforward":   Typeable(code=key_symbols.BROWSER_FORWARD, name='browserforward'),
})

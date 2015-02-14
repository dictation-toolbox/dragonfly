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
"""


import win32con
from dragonfly.actions.keyboard import keyboard, Typeable


#---------------------------------------------------------------------------
# Mapping of name -> typeable.

typeables = {
    # Alphanumeric keys
    "a":                keyboard.get_typeable(char='a'),
    "alpha":            keyboard.get_typeable(char='a'),
    "b":                keyboard.get_typeable(char='b'),
    "bravo":            keyboard.get_typeable(char='b'),
    "c":                keyboard.get_typeable(char='c'),
    "charlie":          keyboard.get_typeable(char='c'),
    "d":                keyboard.get_typeable(char='d'),
    "delta":            keyboard.get_typeable(char='d'),
    "e":                keyboard.get_typeable(char='e'),
    "echo":             keyboard.get_typeable(char='e'),
    "f":                keyboard.get_typeable(char='f'),
    "foxtrot":          keyboard.get_typeable(char='f'),
    "g":                keyboard.get_typeable(char='g'),
    "golf":             keyboard.get_typeable(char='g'),
    "h":                keyboard.get_typeable(char='h'),
    "hotel":            keyboard.get_typeable(char='h'),
    "i":                keyboard.get_typeable(char='i'),
    "india":            keyboard.get_typeable(char='i'),
    "j":                keyboard.get_typeable(char='j'),
    "juliet":           keyboard.get_typeable(char='j'),
    "k":                keyboard.get_typeable(char='k'),
    "kilo":             keyboard.get_typeable(char='k'),
    "l":                keyboard.get_typeable(char='l'),
    "lima":             keyboard.get_typeable(char='l'),
    "m":                keyboard.get_typeable(char='m'),
    "mike":             keyboard.get_typeable(char='m'),
    "n":                keyboard.get_typeable(char='n'),
    "november":         keyboard.get_typeable(char='n'),
    "o":                keyboard.get_typeable(char='o'),
    "oscar":            keyboard.get_typeable(char='o'),
    "p":                keyboard.get_typeable(char='p'),
    "papa":             keyboard.get_typeable(char='p'),
    "q":                keyboard.get_typeable(char='q'),
    "quebec":           keyboard.get_typeable(char='q'),
    "r":                keyboard.get_typeable(char='r'),
    "romeo":            keyboard.get_typeable(char='r'),
    "s":                keyboard.get_typeable(char='s'),
    "sierra":           keyboard.get_typeable(char='s'),
    "t":                keyboard.get_typeable(char='t'),
    "tango":            keyboard.get_typeable(char='t'),
    "u":                keyboard.get_typeable(char='u'),
    "uniform":          keyboard.get_typeable(char='u'),
    "v":                keyboard.get_typeable(char='v'),
    "victor":           keyboard.get_typeable(char='v'),
    "w":                keyboard.get_typeable(char='w'),
    "whisky":           keyboard.get_typeable(char='w'),
    "x":                keyboard.get_typeable(char='x'),
    "xray":             keyboard.get_typeable(char='x'),
    "y":                keyboard.get_typeable(char='y'),
    "yankee":           keyboard.get_typeable(char='y'),
    "z":                keyboard.get_typeable(char='z'),
    "zulu":             keyboard.get_typeable(char='z'),
    "A":                keyboard.get_typeable(char='A'),
    "Alpha":            keyboard.get_typeable(char='A'),
    "B":                keyboard.get_typeable(char='B'),
    "Bravo":            keyboard.get_typeable(char='B'),
    "C":                keyboard.get_typeable(char='C'),
    "Charlie":          keyboard.get_typeable(char='C'),
    "D":                keyboard.get_typeable(char='D'),
    "Delta":            keyboard.get_typeable(char='D'),
    "E":                keyboard.get_typeable(char='E'),
    "Echo":             keyboard.get_typeable(char='E'),
    "F":                keyboard.get_typeable(char='F'),
    "Foxtrot":          keyboard.get_typeable(char='F'),
    "G":                keyboard.get_typeable(char='G'),
    "Golf":             keyboard.get_typeable(char='G'),
    "H":                keyboard.get_typeable(char='H'),
    "Hotel":            keyboard.get_typeable(char='H'),
    "I":                keyboard.get_typeable(char='I'),
    "India":            keyboard.get_typeable(char='I'),
    "J":                keyboard.get_typeable(char='J'),
    "Juliet":           keyboard.get_typeable(char='J'),
    "K":                keyboard.get_typeable(char='K'),
    "Kilo":             keyboard.get_typeable(char='K'),
    "L":                keyboard.get_typeable(char='L'),
    "Lima":             keyboard.get_typeable(char='L'),
    "M":                keyboard.get_typeable(char='M'),
    "Mike":             keyboard.get_typeable(char='M'),
    "N":                keyboard.get_typeable(char='N'),
    "November":         keyboard.get_typeable(char='N'),
    "O":                keyboard.get_typeable(char='O'),
    "Oscar":            keyboard.get_typeable(char='O'),
    "P":                keyboard.get_typeable(char='P'),
    "Papa":             keyboard.get_typeable(char='P'),
    "Q":                keyboard.get_typeable(char='Q'),
    "Quebec":           keyboard.get_typeable(char='Q'),
    "R":                keyboard.get_typeable(char='R'),
    "Romeo":            keyboard.get_typeable(char='R'),
    "S":                keyboard.get_typeable(char='S'),
    "Sierra":           keyboard.get_typeable(char='S'),
    "T":                keyboard.get_typeable(char='T'),
    "Tango":            keyboard.get_typeable(char='T'),
    "U":                keyboard.get_typeable(char='U'),
    "Uniform":          keyboard.get_typeable(char='U'),
    "V":                keyboard.get_typeable(char='V'),
    "Victor":           keyboard.get_typeable(char='V'),
    "W":                keyboard.get_typeable(char='W'),
    "Whisky":           keyboard.get_typeable(char='W'),
    "X":                keyboard.get_typeable(char='X'),
    "Xray":             keyboard.get_typeable(char='X'),
    "Y":                keyboard.get_typeable(char='Y'),
    "Yankee":           keyboard.get_typeable(char='Y'),
    "Z":                keyboard.get_typeable(char='Z'),
    "Zulu":             keyboard.get_typeable(char='Z'),
    "0":                keyboard.get_typeable(char='0'),
    "zero":             keyboard.get_typeable(char='0'),
    "1":                keyboard.get_typeable(char='1'),
    "one":              keyboard.get_typeable(char='1'),
    "2":                keyboard.get_typeable(char='2'),
    "two":              keyboard.get_typeable(char='2'),
    "3":                keyboard.get_typeable(char='3'),
    "three":            keyboard.get_typeable(char='3'),
    "4":                keyboard.get_typeable(char='4'),
    "four":             keyboard.get_typeable(char='4'),
    "5":                keyboard.get_typeable(char='5'),
    "five":             keyboard.get_typeable(char='5'),
    "6":                keyboard.get_typeable(char='6'),
    "six":              keyboard.get_typeable(char='6'),
    "7":                keyboard.get_typeable(char='7'),
    "seven":            keyboard.get_typeable(char='7'),
    "8":                keyboard.get_typeable(char='8'),
    "eight":            keyboard.get_typeable(char='8'),
    "9":                keyboard.get_typeable(char='9'),
    "nine":             keyboard.get_typeable(char='9'),

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

    # Whitespace and editing keys
    "enter":            Typeable(code=win32con.VK_RETURN, name='enter'),
    "tab":              Typeable(code=win32con.VK_TAB, name='tab'),
    "space":            Typeable(code=win32con.VK_SPACE, name='space'),
    "backspace":        Typeable(code=win32con.VK_BACK, name='backspace'),
    "delete":           Typeable(code=win32con.VK_DELETE, name='delete'),
    "del":              Typeable(code=win32con.VK_DELETE, name='del'),

    # Modifier keys
    "shift":            Typeable(code=win32con.VK_SHIFT, name='shift'),
    "control":          Typeable(code=win32con.VK_CONTROL, name='control'),
    "ctrl":             Typeable(code=win32con.VK_CONTROL, name='ctrl'),
    "alt":              Typeable(code=win32con.VK_MENU, name='alt'),

    # Special keys
    "escape":           Typeable(code=win32con.VK_ESCAPE, name='escape'),
    "insert":           Typeable(code=win32con.VK_INSERT, name='insert'),
    "pause":            Typeable(code=win32con.VK_PAUSE, name='pause'),
    "win":              Typeable(code=win32con.VK_LWIN, name='win'),
    "apps":             Typeable(code=win32con.VK_APPS, name='apps'),
    "popup":            Typeable(code=win32con.VK_APPS, name='popup'),

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

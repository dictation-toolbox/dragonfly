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
    This file automates the creation of the typeables.py file.
"""


from ctypes import windll, c_char
import win32con


#---------------------------------------------------------------------------
# 

def parse(input):
    output = []
    for item in input.split(";"):
        parts = item.split("=")
        left_string = parts[0].strip()
        if not left_string: continue
        for right_string in parts[1].split(","):
            right_string = right_string.strip()
            if not right_string: continue
            output.append((left_string, right_string))
    return output


#---------------------------------------------------------------------------
# 

constant_keys ="""
    shift = shift; control = control, ctrl; menu = alt;
    up = up; down = down; left = left; right = right;
    prior = pgup;
    next = pgdown;
    home = home;
    end = end;
    return = enter;
    tab = tab;
    space = space;
    back = backspace;
    delete = delete, del;
    apps = apps, popup;
    escape = escape;

    multiply = npmul;
    add = npadd;
    separator = npsep;
    subtract = npsub;
    decimal = npdec;
    divide = npdiv;
""" \
    + " ".join(["numpad%(n)d = np%(n)d, numpad%(n)d;" % {"n": n} for n in range(10)]) \
    + " ".join(["f%(n)d = f%(n)d;" % {"n": n} for n in range(1, 25)])

for virtual_name, name in parse(constant_keys):
    virtual_name = "VK_%s" % (virtual_name.upper())
    keycode = getattr(win32con, virtual_name)
    print '    "%s": %sTypeable(code=win32con.%s, %sname="%s"),' % (name, " "*(12-len(name)), virtual_name, " "*(12-len(virtual_name)), name)


#---------------------------------------------------------------------------
# 

lookup_keys = r"""
    a = alpha, a; b = bravo, b; c = charlie, c; d = delta, d;
    e = echo, e; f = foxtrot, f; g = golf, g; h = hotel, h;
    i = india, i; j = juliet, j; k = kilo, k; l = lima, l;
    m = mike, m; n = november, n; o = oscar, o; p = papa, p;
    q = quebec, q; r = romeo, r; s = sierra, s; t = tango, t;
    u = uniform, u; v = victor, v; w = whisky, w; x = xray, x;

    y = yankee, y; z = zulu, z;
    A = Alpha, A; B = Bravo, B; C = Charlie, C; D = Delta, D;
    E = Echo, E; F = Foxtrot, F; G = Golf, G; H = Hotel, H;
    I = India, I; J = Juliet, J; K = Kilo, K; L = Lima, L;
    M = Mike, M; N = November, N; O = Oscar, O; P = Papa, P;
    Q = Quebec, Q; R = Romeo, R; S = Sierra, S; T = Tango, T;
    U = Uniform, U; V = Victor, V; W = Whisky, W; X = Xray, X;
    Y = Yankee, Y; Z = Zulu, Z;

    0 = 0, zero; 1 = 1, one; 2 = 2, two; 3 = 3, three; 4 = 4, four;
    5 = 5, five; 6 = 6, six; 7 = 7, seven; 8 = 8, eight; 9 = 9, nine;

    ! = bang, exclamation;  @ = at;  # = hash;  $ = dollar;
    % = percent;  ^ = caret;  & = and, ampersand;  * = star, asterisk; 
    ( = leftparen, lparen; ) = rightparen, rparen;

    - = minus, hyphen;
    _ = underscore; + = plus; ` = backtick; ~ = tilde;
    [ = leftbracket, lbracket; ] = rightbracket, rbracket;
    { = leftbrace, lbrace; } = rightbrace, rbrace;
    \ = backslash; | = bar;
    : = colon;
    ' = apostrophe, singlequote, squote; " = quote, doublequote, dquote;
    , = comma; . = dot; / = slash;
    < = lessthan, leftangle, langle; > = greaterthan, rightangle, rangle;
    ? = question;
"""

for character, name in parse(lookup_keys):
    print '    "%s": %skeyboard.get_typeable(char=%r),' \
        % (name, " "*(12-len(name)),  character)

character = "="
for name in ("equal", "equals"):
    print '    "%s": %skeyboard.get_typeable(char=%r),' \
        % (name, " "*(12-len(name)),  character)

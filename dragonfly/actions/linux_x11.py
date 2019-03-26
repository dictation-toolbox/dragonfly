# Linux implementations of actions using xdotool
# Copied from aenea by Alex Roper
# Integrated with dragonfly by DWK, 2019

import logging
import os
import subprocess

import time

config = {
    'XDOTOOL_DELAY': 0,
    'ENABLE_XSEL': False
}

_MOUSE_BUTTONS = {
    'left': 1,
    'middle': 2,
    'right': 3,
    'wheelup': 4,
    'wheeldown': 5
}


_MOUSE_CLICKS = {
    'click': 'click',
    'down': 'mousedown',
    'up': 'mouseup'
}


_KEY_PRESSES = {
    'press': '',
    'up': 'up',
    'down': 'down'
}


_MOUSE_MOVE_COMMANDS = {
    'absolute': 'mousemove',
    'relative': 'mousemove_relative',
    'relative_active': 'mousemove_active'
}


_SERVER_INFO = {
    'window_manager': 'awesome',
    'operating_system': 'linux',
    'platform': 'linux',
    'display': 'X11',
    'server': 'aenea_reference',
    'server_version': 1
}


_XPROP_PROPERTIES = {
    '_NET_WM_DESKTOP(CARDINAL)': 'desktop',
    'WM_WINDOW_ROLE(STRING)': 'role',
    '_NET_WM_WINDOW_TYPE(ATOM)': 'type',
    '_NET_WM_PID(CARDINAL)': 'pid',
    'WM_LOCALE_NAME(STRING)': 'locale',
    'WM_CLIENT_MACHINE(STRING)': 'client_machine',
    'WM_NAME(STRING)': 'name'
}


_MOD_TRANSLATION = {
    'alt': 'Alt_L',
    'shift': 'Shift_L',
    'control': 'Control_L',
    'super': 'Super_L',
    'hyper': 'Hyper_L',
    'meta': 'Meta_L',
    'win': 'Super_L',
    'flag': 'Super_L',
}


_KEY_TRANSLATION = {
    'ampersand': 'ampersand',
    'apostrophe': 'apostrophe',
    'apps': 'Menu',
    'asterisk': 'asterisk',
    'at': 'at',
    'backslash': 'backslash',
    'backspace': 'BackSpace',
    'backtick': 'grave',
    'bar': 'bar',
    'caret': 'asciicircum',
    'colon': 'colon',
    'comma': 'comma',
    'del': 'Delete',
    'delete': 'Delete',
    'dollar': 'dollar',
    'dot': 'period',
    'dquote': 'quotedbl',
    'enter': 'Return',
    'equal': 'equal',
    'equals': 'equal',
    'exclamation': 'exclam',
    'hash': 'numbersign',
    'hyphen': 'minus',
    'langle': 'less',
    'lbrace': 'braceleft',
    'lbracket': 'bracketleft',
    'lparen': 'parenleft',
    'minus': 'minus',
    'npadd': 'KP_Add',
    'npdec': 'KP_Decimal',
    'npdiv': 'KP_Divide',
    'npmul': 'KP_Multiply',
    'percent': 'percent',
    'pgdown': 'Next',
    'pgup': 'Prior',
    'plus': 'plus',
    'question': 'question',
    'rangle': 'greater',
    'rbrace': 'braceright',
    'rbracket': 'bracketright',
    'rparen': 'parenright',
    'semicolon': 'semicolon',
    'shift': 'Shift_L',
    'slash': 'slash',
    'space': 'space',
    'squote': 'apostrophe',
    'tilde': 'asciitilde',
    'underscore': 'underscore',
    'win': 'Super_L',
}

MORE_KEYS = {
    '!':     "exclamation",
    '@':     "at",
    '#':     "hash",
    '$':     "dollar",
    '%':     "percent",
    '^':     "caret",
    '&':     "ampersand",
    '*':     "asterisk",
    '(':     "lparen",
    ')':     "rparen",
    '-':     "hyphen",
    '_':     "underscore",
    '+':     "plus",
    '`':     "backtick",
    '~':     "tilde",
    '[':     "lbracket",
    ']':     "rbracket",
    '{':     "lbrace",
    '}':     "rbrace",
    '\\':    "backslash",
    '|':     "bar",
    ':':     "colon",
    ';':     "semicolon",
    "'":     "squote",
    '"':     "dquote",
    ',':     "comma",
    '.':     "dot",
    '/':     "slash",
    '<':     "langle",
    '>':     "rangle",
    '?':     "question",
    '=':     "equal",
}
for key in MORE_KEYS:
    value = MORE_KEYS[key]
    if value in _KEY_TRANSLATION:
        translation = _KEY_TRANSLATION[value]
        _KEY_TRANSLATION[key] = translation


def update_key_translation(translation):
    caps_keys = [
        'left',
        'right',
        'up',
        'down',
        'home',
        'end',
        'tab',
        'insert',
        'escape'
    ]
    caps_keys.extend('f%i' % i for i in xrange(1, 13))
    for key in caps_keys:
        translation[key] = key[0].upper() + key[1:]
    for index in xrange(10):
        translation['np%i' % index] = 'KP_%i' % index
    for c in range(ord('a'), ord('z')) + range(ord('0'), ord('9')):
        translation[chr(c)] = chr(c)
        translation[chr(c).upper()] = chr(c).upper()
update_key_translation(_KEY_TRANSLATION)


class XdotoolBackend:
    """
    Implement all of Aenea's RPCs via shelling out to xdotool, xsel, and xprop
    """
    def __init__(self, xdotool='xdotool'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.xdotool = xdotool
        self.xdotool_delay = getattr(config, 'XDOTOOL_DELAY', 0)

    def run_command(self, command, executable=None):
        executable = executable or self.xdotool
        command_string = '%s %s' % (executable, command)
        self.logger.debug(command_string)
        os.system(command_string)

    def read_command(self, command, executable=None):
        executable = executable or self.xdotool
        self.logger.debug('%s %s | <server>' % (executable, command))
        with os.popen('%s %s' % (executable, command), 'r') as fd:
            rval = fd.read()
        return rval

    def write_command(self, message, arguments='type --file -',
                      executable=None):
        executable = executable or self.xdotool
        self.logger.debug(
                'echo \'%s\' | %s %s' % (message, executable, arguments))
        with os.popen('%s %s' % (executable, arguments), 'w') as fd:
            fd.write(message.encode('utf-8'))

    def flush_xdotool(self, actions):
        if actions:
            self.run_command(' '.join(actions))
            del actions[:]

    def server_info(self, _xdotool=None):
        self.flush_xdotool(_xdotool)
        return _SERVER_INFO

    def get_active_window(self, _xdotool=None):
        '''Returns the window id and title of the active window.'''

        self.flush_xdotool(_xdotool)
        window_id = self.read_command('getactivewindow')
        if window_id:
            window_id = int(window_id)
            window_title = self.read_command(
                    'getwindowname %i' % window_id
            ).strip()
            return window_id, window_title
        else:
            return None, None

    def get_geometry(self, window_id=None, _xdotool=None):
        self.flush_xdotool(_xdotool)
        if window_id is None:
            window_id, _ = self.get_active_window()
        geometry = self.read_command('getwindowgeometry --shell %i' % window_id)
        geometry = geometry.strip().split('\n')
        geo = dict([val.lower()
                    for val in line.split('=')]
                   for line in geometry)
        geo = dict((key, int(value)) for (key, value) in geo.iteritems())
        relevant_keys = 'x', 'y', 'width', 'height', 'screen'
        return dict((key, geo[key]) for key in relevant_keys)

    def transform_relative_mouse_event(self, event):
        geo = self.get_geometry()
        dx, dy = map(int, map(float, event.split()))
        return [('mousemove', '%i %i' % (geo['x'] + dx, geo['y'] + dy))]

    def get_context(self, _xdotool=None):
        '''return a dictionary of window properties for the currently active
           window. it is fine to include platform specific information, but
           at least include title and executable.'''

        self.flush_xdotool(_xdotool)
        window_id, window_title = self.get_active_window()
        if window_id is None:
            return {}

        properties = {
            'id': window_id,
            'title': window_title,
        }
        for line in self.read_command('-id %s' % window_id, 'xprop').split('\n'):
            split = line.split(' = ', 1)
            if len(split) == 2:
                rawkey, value = split
                if split[0] in _XPROP_PROPERTIES:
                    property_value = value[1:-1] if '(STRING)' in rawkey else value
                    properties[_XPROP_PROPERTIES[rawkey]] = property_value
                elif rawkey == 'WM_CLASS(STRING)':
                    window_class_name, window_class = value.split('", "')
                    properties['cls_name'] = window_class_name[1:]
                    properties['cls'] = window_class[:-1]

        # Sigh...
        properties['executable'] = None
        properties['executable'] = None
        if 'pid' in properties:
            try:
                proc_command = '/proc/%s/exe' % properties['pid']
                properties['executable'] = os.readlink(proc_command)
            except OSError:
                ps = self.read_command('%s' % properties['pid'], executable='ps')
                ps = ps.split('\n')[1:]
                if ps:
                    try:
                        properties['executable'] = ps[0].split()[4]
                    except Exception:
                        pass

            try:
                cmdline_path = '/proc/%s/cmdline' % properties['pid']
                with open(cmdline_path) as fd:
                    properties['cmdline'] = fd.read().replace('\x00', ' ').strip()
            except (IOError, OSError):
                pass
        else:
            self.logger.warn('pid not set. properties: %s' % properties)
        return properties

    def pause(self, amount, _xdotool=None):
        '''pause amount in ms.'''
        if _xdotool is not None:
            _xdotool.append('sleep %f' % (amount / 1000.))
        else:
            time.sleep(amount / 1000.)

    def notify(self, message):
        '''Send a message to the notification daemon via notify-send.'''
        try:
            subprocess.Popen(['notify-send', message])
        except Exception as e:
            self.logger.warn('failed to start notify-send process: %s' % e)

    def move_mouse(self, x, y, reference='absolute', proportional=False,
                   phantom=None, _xdotool=None):
        '''move the mouse to the specified coordinates. reference may be one
        of 'absolute', 'relative', or 'relative_active'. if phantom is not
        None, it is a button as click_mouse. If possible, click that
        location without moving the mouse. If not, the server will move the
        mouse there and click. Currently, phantom only works with absolute
        moves. Negative coordinates are allowed for all references; in the
        case of absolute they will be clamped to 0.'''

        geo = self.get_geometry()
        if proportional:
            x = geo['width'] * x
            y = geo['height'] * y
        command = _MOUSE_MOVE_COMMANDS[reference]
        if command == 'mousemove_active':
            command = 'mousemove --window %i' % self.get_active_window()[0]

        if x <= 0 or y <= 0:
            commands = ['%s -- %f %f' % (command, x, y)]
        else:
            commands = ['%s %f %f' % (command, x, y)]
        if phantom is not None:
            commands.append('click %s' % _MOUSE_BUTTONS[phantom])
            commands.append('mousemove restore')

        # To avoid headaches down the road with argparse, we don't chain commands
        # if we need to use -- since it would block future flags from being
        # interpreted.
        if _xdotool is not None and x >= 0 and y >= 0:
            _xdotool.extend(commands)
        else:
            self.flush_xdotool(_xdotool)
            self.run_command(' '.join(commands))

    def click_mouse(self, button, direction='click', count=1, count_delay=None,
                    _xdotool=None):
        '''click the mouse button specified. button maybe one of 'right',
           'left', 'middle', 'wheeldown', 'wheelup'. This X11 server will
           also accept a number.'''

        if count_delay is None or count < 2:
            delay = ''
        else:
            delay = '--delay %i ' % count_delay

        repeat = '' if count == 1 else '--repeat %i' % count

        try:
            button = _MOUSE_BUTTONS[button]
        except KeyError:
            button = int(button)

        command = ('%s %s %s %s' %
                   (_MOUSE_CLICKS[direction], delay, repeat, button))

        if _xdotool is not None:
            _xdotool.append(command)
        else:
            self.run_command(command)


    def write_text(self, text, paste=False, _xdotool=None):
        '''send text formatted exactly as written to active window. If paste
           is True, will use X11 PRIMARY clipboard to paste the text instead
           of typing it. See config.ENABLE_XSEL documentation for more
           information on this.'''

        # Workaround for https://github.com/jordansissel/xdotool/pull/29
        if text:
            if paste and config.ENABLE_XSEL:
                # swap primary and secondary X11 clipboards so we can
                # restore after paste
                self.run_command('-x', executable='xsel')

                # copy the pasted text to the clipboard
                self.write_command(text, arguments='-i', executable='xsel')

                # paste by simulating middle click
                # TODO: can we do this even in programs that don't have a
                #     middle click?
                #     if not, we may need a blacklist of buggy programs.
                self.click_mouse(2, _xdotool=_xdotool)
                self.flush_xdotool(_xdotool)

                # nuke the text we selected
                self.run_command('-c', executable='xsel')

                # restore the previous clipboard contents
                self.run_command('-x', executable='xsel')
            else:
                self.flush_xdotool(_xdotool)

                self.write_command(
                        text,
                        arguments='type --file - --delay %d' % self.xdotool_delay
                )

    def key_press(self, key=None, modifiers=(), direction='press', count=1,
                  count_delay=None, _xdotool=None):
        '''press a key possibly modified by modifiers. direction may be
           'press', 'down', or 'up'. modifiers may contain 'alt', 'shift',
           'control', 'super'. this X11 server also supports 'hyper',
           'meta', and 'flag' (same as super). count is number of times to
           press it. count_delay delay in ms between presses.'''
        assert key is not None

        if count_delay is None or count < 2:
            delay = ''
        else:
            delay = '--delay %i ' % count_delay

        modifiers = [_MOD_TRANSLATION.get(mod, mod) for mod in modifiers]
        key_to_press = _KEY_TRANSLATION.get(key, key)

        keys = ['keydown ' + k for k in modifiers]
        keys.extend(['key%s %s %s' % (_KEY_PRESSES[direction], delay, key_to_press)] * count)
        keys.extend('keyup ' + k for k in reversed(modifiers))

        if _xdotool is not None:
            _xdotool.extend(keys)
        else:
            self.run_command(' '.join(keys))

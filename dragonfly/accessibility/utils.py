"""This module contains OS-independent functionality *which does not depend on
other Dragonfly functionality*. Functionality which does depend on Dragonfly
classes such as actions should go into controller.py. This separation is done to
make it easier in the future to extract this functionality as a general Python
library independent of Dragonfly.
"""


import regex
import enum
import logging


_log = logging.getLogger("accessibility")


class CursorPosition(enum.Enum):
    """The cursor position relative to a range of text."""

    BEFORE = 1
    """The position before the text."""

    AFTER = 2
    """The position after the text."""


class TextQuery(object):
    """A query to match a range of text."""

    def __init__(self,
                 start_phrase="",
                 start_relative_position=None,
                 start_relative_phrase="",
                 through=False,
                 end_phrase="",
                 end_relative_position=None,
                 end_relative_phrase=""):
        if not (end_phrase or end_relative_phrase):
            raise ValueError("Must specify end (relative) phrase")
        if not through and (start_phrase or start_relative_phrase):
            raise ValueError("Must specify 'through' if start is specified.")
        if start_relative_phrase and not start_relative_position:
            raise ValueError("Must specify before or after for start_relative_phrase")
        if end_relative_phrase and not end_relative_position:
            raise ValueError("Must specify before or after for end_relative_phrase")

        self.start_phrase = start_phrase
        """The phrase at the start of the match."""

        self.start_relative_position = start_relative_position
        """Whether to match before or after the :attr:`start_relative_phrase`."""

        self.start_relative_phrase = start_relative_phrase
        """The phrase to match before or after at the start."""

        self.through = through
        """True if matching from a start point to the end phrase."""

        self.end_phrase = end_phrase
        """The phrase at the end of the match (or the sole phrase)."""

        self.end_relative_position = end_relative_position
        """Whether to match before or after the :attr:`end_relative_phrase`."""

        self.end_relative_phrase = end_relative_phrase
        """The phrase to match before or after at the end."""

    def __repr__(self):
        return str(dict([(k, v) for (k, v) in self.__dict__.items() if v]))


class TextInfo(object):
    """Information about a range of text."""

    def __init__(self, start, end, text, start_coordinates=None, end_coordinates=None):
        self.start = start
        self.end = end
        self.text = text
        self.start_coordinates = start_coordinates
        self.end_coordinates = end_coordinates


def _phrase_to_regex(phrase):
    # Treat whitespace between words as meaning anything other than alphanumeric
    # characters.
    pattern = r"[^\w--_]+".join(regex.escape(word) for word in phrase.split())
    # Treat spaces at the beginning or end of the phrase as matching any
    # whitespace character. This makes it easy to select stuff like non-breaking
    # space, which occurs frequently in browsers.
    # TODO Support newlines. Note that these are frequently implemented as
    # separate text nodes in the accessibility tree, so the obvious
    # implementation would not work well.
    if phrase == " ":
        pattern = r"\s"
    else:
        if phrase.startswith(" "):
            pattern = r"\s" + pattern
        if phrase.endswith(" "):
            pattern = pattern + r"\s"
    # Only match at boundaries of alphanumeric sequences if the phrase ends
    # are alphanumeric.
    if regex.search(r"^[\w--_]", phrase, regex.VERSION1 | regex.UNICODE):
        pattern = r"(?<![\w--_])" + pattern
    if regex.search(r"[\w--_]$", phrase, regex.VERSION1 | regex.UNICODE):
        pattern = pattern + r"(?![\w--_])"
    return pattern


def _find_text(query, expanded_text, cursor_offset):
    # Convert query to regex with a single matching group. Note that this used
    # to be simpler but buggy, and is now is complicated because lookbehind and
    # lookahead regular expressions must be fixed-width, so we have to limit
    # their usage and use a matching group instead, which requires matching up
    # the parens surrounding the group.
    pattern = r""

    # Add the start phrases, if present.
    if query.start_phrase or query.start_relative_phrase:
        if query.start_relative_phrase and query.start_relative_position == CursorPosition.AFTER:
            pattern += _phrase_to_regex(query.start_relative_phrase)
            if query.start_phrase:
                pattern += r"[^\w--_]*"
        pattern += r"(" + _phrase_to_regex(query.start_phrase)
        if query.start_relative_phrase and query.start_relative_position == CursorPosition.BEFORE:
            if query.start_phrase:
                pattern += r"[^\w--_]*"
            pattern += _phrase_to_regex(query.start_relative_phrase)
        pattern += r".*?"

    # Add the end phrases.
    if query.end_relative_phrase and query.end_relative_position == CursorPosition.AFTER:
        pattern += _phrase_to_regex(query.end_relative_phrase)
        if query.end_phrase:
            pattern += r"[^\w--_]*"
    # Add the initial "(" if we haven't already.
    if not (query.start_phrase or query.start_relative_phrase):
        pattern += r"("
    pattern += _phrase_to_regex(query.end_phrase) + r")"
    if query.end_relative_phrase and query.end_relative_position == CursorPosition.BEFORE:
        if query.end_phrase:
            pattern += r"[^\w--_]*"
        pattern += _phrase_to_regex(query.end_relative_phrase)

    # Find all matches.
    matches = regex.finditer(pattern,
                             expanded_text,
                             regex.IGNORECASE | regex.VERSION1 | regex.UNICODE,
                             overlapped=True)
    ranges = [(match.start(1), match.end(1)) for match in matches]
    if not ranges:
        _log.warning("Not found: %s" % query)
        return None
    start_with_cursor = (query.through and not (query.start_phrase or query.start_relative_phrase))
    if cursor_offset is None:
        _log.warning("Cursor not found.")
        if start_with_cursor:
            _log.warning("Cannot perform cursor-relative query without cursor.")
            return None
        else:
            # Pick arbitrary match (the first one).
            return ranges[0]
    else:
        # Find nearest match.
        range = min(ranges, key=lambda x: abs((x[0] + x[1]) / 2 - cursor_offset))
        if start_with_cursor:
            if range[0] < cursor_offset:
                return (range[0], cursor_offset)
            else:
                return (cursor_offset, range[1])
        else:
            return range


def _get_focused_text(context):
    if not context.focused:
        _log.warning("Nothing is focused.")
        return None
    focused_text = context.focused.as_text()
    if not focused_text:
        _log.warning("Focused element is not text.")
        return None
    return focused_text


def get_cursor_offset(controller):
    def closure(context):
        focused_text = _get_focused_text(context)
        if not focused_text:
            return None
        return focused_text.cursor
    return controller.run_sync(closure)


def set_cursor_offset(controller, offset):
    def closure(context):
        focused_text = _get_focused_text(context)
        if not focused_text:
            return None
        focused_text.set_cursor(offset)
    controller.run_sync(closure)


def get_text_info(controller, query):
    _log.debug("Getting text info: %s" % query)
    def closure(context):
        focused_text = _get_focused_text(context)
        if not focused_text:
            return None
        nearest = _find_text(query, focused_text.expanded_text, focused_text.cursor)
        if not nearest:
            return None
        text_info = TextInfo(nearest[0], nearest[1],
                             focused_text.expanded_text[nearest[0]:nearest[1]])
        start_box = focused_text.get_bounding_box(nearest[0])
        end_box = focused_text.get_bounding_box(nearest[1] - 1)
        # Ignore offscreen coordinates. Google Docs returns these, and we handle
        # it here to avoid further trouble.
        if start_box.x < 0 or start_box.y < 0 or end_box.x < 0 or end_box.y < 0:
            _log.warning("Text selection points were offscreen, ignoring.")
        else:
            text_info.start_coordinates = start_box.x, start_box.y + start_box.height / 2
            text_info.end_coordinates = end_box.x + end_box.width, end_box.y + end_box.height / 2
        return text_info
    return controller.run_sync(closure)


def move_cursor(controller, query, position):
    """Moves the cursor before or after the provided phrase."""

    _log.info("Moving cursor %s phrase: %s" % (position.name, query))
    def closure(context):
        focused_text = _get_focused_text(context)
        if not focused_text:
            return False
        nearest = _find_text(query, focused_text.expanded_text, focused_text.cursor)
        if not nearest:
            return False
        focused_text.set_cursor(nearest[0] if position is CursorPosition.BEFORE else nearest[1])
        _log.info("Moved cursor")
        return True
    return controller.run_sync(closure)


def select_text(controller, query):
    _log.info("Selecting text: %s" % query)
    def closure(context):
        focused_text = _get_focused_text(context)
        if not focused_text:
            return False
        nearest = _find_text(query, focused_text.expanded_text, focused_text.cursor)
        if not nearest:
            return False
        focused_text.select_range(*nearest)
        _log.info("Selected text")
        return True
    return controller.run_sync(closure)


def is_editable_focused(controller):
    """Returns true if an editable object is focused."""

    def closure(context):
        return context.focused and context.focused.is_editable()
    return controller.run_sync(closure)

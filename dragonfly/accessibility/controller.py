from dragonfly import (
    Key,
    Mouse,
    Text,
)

from . import base
from . import utils


class AccessibilityController(object):
    """OS-independent controller for accessing accessibility functionality."""

    def __init__(self, os_controller):
        self.os_controller = os_controller

    def is_editable_focused(self):
        return utils.is_editable_focused(self.os_controller)

    def move_cursor(self, text_query, position):
        return utils.move_cursor(self.os_controller, text_query, position)

    def select_text(self, text_query):
        try:
            return utils.select_text(self.os_controller, text_query)
        except base.UnsupportedSelectionError:
            # Fall back to mouse-based text selection.
            text_info = utils.get_text_info(self.os_controller, text_query)
            if text_info and text_info.start_coordinates and text_info.end_coordinates:
                Mouse("[%d, %d], left:down, [%d, %d]/10, left:up" %
                      (text_info.start_coordinates + text_info.end_coordinates)).execute()
                return True
            else:
                return False

    def replace_text(self, text_query, replacement):
        saved_cursor = utils.get_cursor_offset(self.os_controller)
        text_info = utils.get_text_info(self.os_controller, text_query)
        if not text_info:
            return
        cursor_before = text_info.end
        if self.select_text(text_query):
            # Replace text.
            if replacement:
                replacement = str(replacement).lower()
                if text_info.text.isupper():
                    replacement = replacement.upper()
                elif text_info.text[0].isupper():
                    replacement = replacement.capitalize()
                # TODO Add escaping.
                Text(replacement).execute()
            else:
                # Simulate backspace twice: once to delete the selected words, and
                # again to delete the preceding whitespace.
                Key("backspace:2").execute()

            # Restore cursor position.
            if saved_cursor is not None:
                if saved_cursor <= text_info.start:
                    utils.set_cursor_offset(self.os_controller, saved_cursor)
                elif saved_cursor <= text_info.end:
                    # Saved cursor is within changed region, leave as-is.
                    pass
                else:
                    cursor_after = utils.get_cursor_offset(self.os_controller)
                    if cursor_after:
                        utils.set_cursor_offset(self.os_controller, saved_cursor + cursor_after - cursor_before)

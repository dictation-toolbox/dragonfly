"""This file contains the IAccessible2-based accessibility controller
implementation for Windows.
"""


import logging
import threading
import traceback
import time

from six.moves import queue

from . import base


class Controller(object):
    """Provides access to the IAccessible2 subsystem. All accesses to this subsystem
    must be run in a single thread, which is managed here."""

    _log = logging.getLogger("accessibility")

    class Capture(object):
        def __init__(self, closure):
            self.closure = closure
            self.done_event = threading.Event()
            self.exception = None
            self.return_value = None

    def __init__(self):
        self._context = Context()
        # TODO Replace with a completely synchronous queue (size 0).
        self._closure_queue = queue.Queue(1)
        self._focus_queue = []

    def _update_focus(self, event):
        # Add event to a queue for later processing. IAccessible2 functions can
        # cause reentrancy into event handling, so we do this to ensure correct
        # order of processing.
        self._focus_queue.append(event)

    def _process_focus_events(self):
        if not self._focus_queue:
            return

        # Get the latest focus event, skipping obsolete events.
        if len(self._focus_queue) > 1:
            self._log.debug("Skipping %s focus events." % (len(self._focus_queue) - 1))
        event = self._focus_queue[-1]
        self._focus_queue = []

        accessible_start = time.time()
        accessible = pyia2.accessibleObjectFromEvent(event)
        self._log.debug("Attempted to convert to accessible: %.10f" % (time.time() - accessible_start))
        if not accessible:
            self._context.focused = None
            return

        accessible2_start = time.time()
        accessible2 = pyia2.accessible2FromAccessible(accessible,
                                                      pyia2.CHILDID_SELF)
        self._log.debug("Attempted to convert to accessible2: %.10f" % (time.time() - accessible2_start))
        if not isinstance(accessible2, pyia2.IA2Lib.IAccessible2):
            self._context.focused = None
            return

        self._context.focused = Accessible(accessible2)
        self._log.debug("Set focused. accessible2: %s" % accessible2)

    def _start_blocking(self):
        # Import here so that it can be used in a background thread. The import
        # must be run in the same thread as event registration and handling.
        global comtypes, pyia2
        import comtypes
        import pyia2

        # Register event listeners.
        pyia2.Registry.registerEventListener(self._update_focus,
                                             pyia2.EVENT_OBJECT_FOCUS)

        # Perform all IAccessible2 operations as they are enqueued.
        while not self.shutdown_event.is_set():
            pyia2.Registry.iter_loop(0.01)

            # Process events.
            try:
                self._process_focus_events()
            except comtypes.COMError:
                # Commonly occurs when the focus event no longer matches an active object.
                pass
            except Exception:
                traceback.print_exc()

            # Process closures.
            while True:
                try:
                    capture = self._closure_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    capture.return_value = capture.closure(self._context)
                except base.AccessibilityError as exception:
                    capture.exception = exception
                    # Checked exception, don't print.
                    pass
                except Exception as exception:
                    capture.exception = exception
                    # The stack trace won't be captured, so print here.
                    traceback.print_exc()
                capture.done_event.set()

        # Deregister event listeners.
        pyia2.Registry.clearListeners()

    def start(self):
        self.shutdown_event = threading.Event()
        thread = threading.Thread(target=self._start_blocking)
        thread.setDaemon(True)
        thread.start()

    def stop(self):
        self.shutdown_event.set()

    def run_sync(self, closure):
        capture = self.Capture(closure)
        self._closure_queue.put(capture)
        capture.done_event.wait()
        if capture.exception:
            raise capture.exception
        return capture.return_value


class Context(object):
    """Provides access to the current IAccessible2 context, such as focused objects."""

    def __init__(self):
        self.focused = None


class Accessible(object):
    """Wraps an IAccessible2."""

    def __init__(self, accessible):
        self._accessible = accessible

    def as_text(self):
        try:
            text = self._accessible.QueryInterface(pyia2.IA2Lib.IAccessibleText)
            return AccessibleTextNode(text)
        except comtypes.COMError:
            return None

    def is_editable(self):
        return pyia2.IA2_STATE_EDITABLE & self._accessible.states


class BoundingBox(object):
    """Represents a bounding box in screen coordinates."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __str__(self):
        return "x=%s, y=%s, width=%s, height=%s" % (self.x, self.y, self.width, self.height)


class AccessibleTextNode(object):
    """Provides a wrapper around a snapshot of IAccessibleText. Mutable methods will
    affect the underlying IAccessibleText, but the changes will not be reflected
    here."""

    def __init__(self, accessible_text, may_have_cursor=True):
        self.is_leaf = False
        self._text = accessible_text
        self._children = []
        text_length = self._text.nCharacters
        text = self._text.text(0, text_length) if text_length > 0 else ""
        cursor_offset = self._text.caretOffset
        if cursor_offset < 0:
            cursor_offset = None
        expanded_text_pieces = []
        child_indices = [i for i, c in enumerate(text) if c == u"\ufffc"]
        if not child_indices:
            self._add_leaf(0, text_length, text, expanded_text_pieces, cursor_offset)
        elif child_indices[0] > 0:
            self._add_leaf(0, child_indices[0], text, expanded_text_pieces, cursor_offset)
        for i, child_index in enumerate(child_indices):
            # TODO Handle case where all embedded objects are non-text and this interface is not supported.
            hypertext = self._text.QueryInterface(pyia2.IA2Lib.IAccessibleHypertext)
            hyperlink_index = hypertext.hyperlinkIndex(child_index)
            hyperlink = hypertext.hyperlink(hyperlink_index)
            # TODO Handle case where embedded object is non-text.
            child = hyperlink.QueryInterface(pyia2.IA2Lib.IAccessibleText)
            child_node = AccessibleTextNode(child, cursor_offset == child_index)
            self._children.append(child_node)
            expanded_text_pieces.append(child_node.expanded_text)
            end_index = child_indices[i + 1] if i < len(child_indices) - 1 else text_length
            if end_index > child_index + 1:
                self._add_leaf(child_index + 1, end_index, text, expanded_text_pieces, cursor_offset)
        self.expanded_text = "".join(expanded_text_pieces)
        self.cursor = None
        # Only look for cursor if we might have it. This works around a Chrome
        # bug where nodes report the cursor at 0 instead of -1 when they don't
        # have the cursor.
        if may_have_cursor:
            offset = 0
            for child in self._children:
                if child.cursor is not None:
                    self.cursor = offset + child.cursor
                    break;
                offset += len(child.expanded_text)

    def __str__(self):
        return "(" + ", ".join(str(child) for child in self._children) + ")"

    def _add_leaf(self, start, end, text, expanded_text_pieces, cursor_offset):
        child = AccessibleTextLeaf(self._text, text, start, end, cursor_offset)
        self._children.append(child)
        expanded_text_pieces.append(child.expanded_text)

    def set_cursor(self, offset):
        """Sets the cursor to the given offset. Note that the update will not be
        reflected in self.cursor."""

        for child in self._children:
            if offset < len(child.expanded_text):
                child.set_cursor(offset)
                return
            offset -= len(child.expanded_text)

    def get_bounding_box(self, offset):
        for child in self._children:
            if offset < len(child.expanded_text):
                return child.get_bounding_box(offset)
            offset -= len(child.expanded_text)

    def _get_child_and_child_offset(self, offset):
        for child in self._children:
            if offset < len(child.expanded_text):
                return (child, offset)
            offset -= len(child.expanded_text)

    def select_range(self, start, end):
        start_child, start_child_offset = self._get_child_and_child_offset(start)
        end_child, end_child_offset = self._get_child_and_child_offset(end)
        if start_child == end_child and not start_child.is_leaf:
            # Selection is fully contained within a child node.
            start_child.select_range(start_child_offset, end_child_offset)
            return
        if not start_child.is_leaf or not end_child.is_leaf:
            # Selection cannot be made within a single node, which is the only
            # widely supported API.
            raise base.UnsupportedSelectionError()
        # Selection spans one leaf child to another leaf child.
        self._text.setSelection(0,
                                start_child.get_parent_offset(start_child_offset),
                                end_child.get_parent_offset(end_child_offset))


class AccessibleTextLeaf(object):
    """Wrapper around a pure-text segment of an IAccessibleText. Mutable methods
    will affect the underlying IAccessibleText, but the changes will not be
    reflected here."""

    # Use a broken vertical bar at the end of the text to delimit it from other
    # leaf nodes when expanded. This character was chosen because it is
    # printable and rarely used in practice.
    DELIMITER = u"\u00a6"

    def __init__(self, accessible_text, text, start, end, cursor_offset):
        self.is_leaf = True
        self._text = accessible_text
        self.expanded_text = text[start:end] + self.DELIMITER
        self._start = start
        self._end = end
        self.cursor = cursor_offset - start if cursor_offset is not None and cursor_offset >= start and cursor_offset <= end else None

    def __str__(self):
        return self.expanded_text

    def get_parent_offset(self, offset):
        return self._start + offset

    def set_cursor(self, offset):
        """Sets the cursor to the given offset. Note that the update will not be
        reflected in self.cursor."""

        self._text.setCaretOffset(self.get_parent_offset(offset))

    def get_bounding_box(self, offset):
        return BoundingBox(*self._text.characterExtents(
            self.get_parent_offset(offset),
            pyia2.IA2Lib.IA2_COORDTYPE_SCREEN_RELATIVE))

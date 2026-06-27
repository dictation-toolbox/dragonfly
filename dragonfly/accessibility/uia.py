"""UI Automation backend helpers for Dragonfly accessibility."""

import importlib
import logging
import threading
import traceback

from six.moves import queue

from dragonfly.accessibility import base


class _UIAConstants(object):
    TextPatternRangeEndpoint_Start = "start"
    TextPatternRangeEndpoint_End = "end"
    TextUnit_Character = "character"


UIA = _UIAConstants
_log = logging.getLogger("accessibility")


def _load_uia_modules():
    comtypes = importlib.import_module("comtypes")
    comtypes_client = importlib.import_module("comtypes.client")
    try:
        uia_client = importlib.import_module("comtypes.gen.UIAutomationClient")
    except ImportError:
        comtypes_client.GetModule("UIAutomationCore.dll")
        uia_client = importlib.import_module("comtypes.gen.UIAutomationClient")
    return comtypes, comtypes_client, uia_client


def _create_automation():
    global UIA
    _comtypes, comtypes_client, uia_client = _load_uia_modules()
    UIA = uia_client
    return comtypes_client.CreateObject(
        "{ff48dba4-60ef-4201-aa87-54103eef594e}",
        interface=uia_client.IUIAutomation,
    )


def _query_interface(pattern, interface_name):
    if not _is_supported_pattern(pattern):
        return None
    interface = getattr(UIA, interface_name, None)
    if hasattr(pattern, "QueryInterface"):
        try:
            queried_pattern = pattern.QueryInterface(interface)
        except Exception:
            _log.debug("Failed to query %s on %r" % (interface_name, pattern))
            return pattern
        if _is_supported_pattern(queried_pattern):
            return queried_pattern
    return pattern


def _is_supported_pattern(pattern):
    if pattern is None:
        return False
    try:
        return bool(pattern)
    except Exception:
        return True


class Controller(object):

    class Capture(object):

        def __init__(self, closure):
            self.closure = closure
            self.done_event = threading.Event()
            self.exception = None
            self.return_value = None

    def __init__(self):
        _load_uia_modules()
        self._context = Context()
        self._closure_queue = queue.Queue(1)
        self._shutdown_event = threading.Event()
        self._startup_done_event = threading.Event()
        self._startup_exception = None

    def _start_blocking(self):
        try:
            self._context.initialize()
        except Exception as exception:
            self._startup_exception = exception
            self._startup_done_event.set()
            return
        self._startup_done_event.set()
        while not self._shutdown_event.is_set():
            self._context.update_focus()
            try:
                capture = self._closure_queue.get(timeout=0.01)
            except queue.Empty:
                continue
            try:
                capture.return_value = capture.closure(self._context)
            except base.AccessibilityError as exception:
                capture.exception = exception
            except Exception as exception:
                capture.exception = exception
                traceback.print_exc()
            capture.done_event.set()

    def start(self):
        self._shutdown_event.clear()
        self._startup_exception = None
        self._startup_done_event.clear()
        thread = threading.Thread(target=self._start_blocking)
        thread.daemon = True
        thread.start()
        self._startup_done_event.wait()
        if self._startup_exception:
            self._shutdown_event.set()
            raise self._startup_exception

    def stop(self):
        self._shutdown_event.set()

    def run_sync(self, closure):
        capture = self.Capture(closure)
        self._closure_queue.put(capture)
        capture.done_event.wait()
        if capture.exception:
            raise capture.exception
        return capture.return_value


class Context(object):

    def __init__(self, automation=None):
        self.automation = automation
        self.focused = None

    def initialize(self):
        if self.automation is None:
            self.automation = _create_automation()

    def update_focus(self):
        if self.automation is None:
            self.focused = None
            return
        try:
            focused = self.automation.GetFocusedElement()
        except Exception:
            self.focused = None
            return
        self.focused = Accessible(focused) if focused else None


class Accessible(object):

    def __init__(self, element):
        self._element = element

    def as_text(self):
        pattern = self._element.GetCurrentPattern(UIA.UIA_TextPatternId)
        if not _is_supported_pattern(pattern):
            return None
        pattern = _query_interface(pattern, "IUIAutomationTextPattern")
        if not _is_supported_pattern(pattern):
            return None
        return UiaAccessibleTextNode(self._element, pattern)

    def is_editable(self):
        value_pattern = self._element.GetCurrentPattern(UIA.UIA_ValuePatternId)
        if _is_supported_pattern(value_pattern):
            value_pattern = _query_interface(value_pattern, "IUIAutomationValuePattern")
            if _is_supported_pattern(value_pattern):
                return not value_pattern.CurrentIsReadOnly
        return self._element.CurrentControlType in (
            UIA.UIA_EditControlTypeId,
            UIA.UIA_DocumentControlTypeId,
        )


class BoundingBox(object):

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __str__(self):
        return "x=%s, y=%s, width=%s, height=%s" % (
            self.x, self.y, self.width, self.height
        )


class UiaAccessibleTextNode(object):
    """Minimal UIA text-node contract for accessibility controller integration."""

    def __init__(self, element, text_pattern):
        self._element = element
        self._text_pattern = text_pattern
        self._document_range = text_pattern.DocumentRange
        self.expanded_text = self._document_range.GetText(-1)

        selection = text_pattern.GetSelection()
        if selection.Length:
            selected_range = selection.GetElement(0)
            self.cursor = self._get_offset(selected_range)
        else:
            self.cursor = 0

    def _get_collapsed_range_at_start(self):
        collapsed_range = self._document_range.Clone()
        collapsed_range.MoveEndpointByRange(
            UIA.TextPatternRangeEndpoint_End,
            collapsed_range,
            UIA.TextPatternRangeEndpoint_Start,
        )
        return collapsed_range

    def _get_offset(self, text_range):
        offset = 0
        probe = self._get_collapsed_range_at_start()
        # CompareEndpoints only tells us relative ordering, so walk forward
        # from the start of the document to derive a character offset.
        while offset < len(self.expanded_text) and probe.CompareEndpoints(
                UIA.TextPatternRangeEndpoint_Start,
                text_range,
                UIA.TextPatternRangeEndpoint_Start,
        ) < 0:
            moved = probe.Move(UIA.TextUnit_Character, 1)
            if moved <= 0:
                break
            offset += moved
        return offset

    def _make_range(self, start, end):
        start = max(0, min(start, len(self.expanded_text)))
        end = max(start, min(end, len(self.expanded_text)))
        text_range = self._get_collapsed_range_at_start()
        if start:
            text_range.Move(UIA.TextUnit_Character, start)
        if end > start:
            text_range.MoveEndpointByUnit(
                UIA.TextPatternRangeEndpoint_End,
                UIA.TextUnit_Character,
                end - start,
            )
        return text_range

    def select_range(self, start, end):
        range_to_select = self._make_range(start, end)
        range_to_select.Select()

    def set_cursor(self, offset):
        cursor_range = self._make_range(offset, offset)
        cursor_range.Select()
        self.cursor = offset

    def get_bounding_box(self, offset):
        char_range = self._make_range(offset, offset + 1)
        rect = char_range.GetBoundingRectangles()
        return BoundingBox(rect[0], rect[1], rect[2], rect[3])

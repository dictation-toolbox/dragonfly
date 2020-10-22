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

import logging
import threading
import time
import unittest

from dragonfly import (ActionBase, CompoundRule, Grammar, Literal,
                       MappingRule, Rule, get_engine, RPCServer,
                       send_rpc_request)


class CapturingHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class RPCTestCase(unittest.TestCase):
    """
    Tests for RPC server methods.
    """

    @classmethod
    def setUpClass(cls):
        cls.current_response = None

        # Start the server on a different port for the tests.
        cls.server = RPCServer(port=50052)
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def _send_request(self, request_function):
        # Send requests to the server using new threads to emulate requests
        # from a different process.
        request_thread = threading.Thread(target=request_function)
        request_thread.start()

        # Manually process server requests by calling the timer manager's
        # main callback directly.
        while request_thread.is_alive():
            get_engine()._timer_manager.main_callback()
            time.sleep(0.05)

        # Handle errors and results from the request.
        if isinstance(self.current_response, Exception):
            raise self.current_response
        else:
            return self.current_response

    def send_request(self, method, params, id=0):
        def request():
            try:
                self.current_response = self.server.send_request(
                    method, params, id
                )
            except Exception as e:
                self.current_response = e

        return self._send_request(request)

    def test_add_method(self):
        """ Verify that RPC methods can be added and replaced."""
        self.server.add_method(lambda: "bar", "foo")
        response = self.send_request("foo", [])
        self.assertEqual(response, {'jsonrpc': '2.0', 'result': 'bar',
                                    'id': 0})
        self.server.add_method(lambda: "foo", "foo")
        response = self.send_request("foo", [])
        self.assertEqual(response, {'jsonrpc': '2.0', 'result': 'foo',
                                    'id': 0})

    def test_remove_method(self):
        """ Verify that RPC methods can be removed."""
        # The following should not raise an error.
        self.server.remove_method("non_existent")

        # Add a 'bar' method, check that it works.
        self.server.add_method(lambda: "foo", "bar")
        response = self.send_request("bar", [])
        self.assertEqual(response, {'jsonrpc': '2.0', 'result': 'foo',
                                    'id': 0})

        # Remove it and check that an error is returned by the server.
        # 'send_request' will raise a RuntimeError if the server returns an
        # error.
        self.server.remove_method("bar")
        self.assertRaises(RuntimeError,
                          lambda: self.send_request("bar", []))

    def test_errors(self):
        """ Verify that the server handles errors from RPC methods. """
        log_capture = CapturingHandler()
        logger = logging.getLogger("rpc.methods")
        logger.addHandler(log_capture)

        # Add a new RPC method and check if an error is logged and received.
        def error():
            raise RuntimeError("error message")

        self.server.add_method(error, "error")
        try:
            self.assertRaises(RuntimeError,
                              lambda: self.send_request("error", []))
            self.assertEqual(len(log_capture.records), 1)
            log_message = log_capture.records[0].msg
            self.assertTrue("Exception occurred during RPC method" in log_message)
            self.assertTrue("error message" in log_message)
        finally:
            logger.removeHandler(log_capture)

    def test_security_tokens(self):
        """ Verify that security tokens must match for RPC execution to occur.
        """
        logger = logging.getLogger("rpc.methods")

        # Add an RPC method for testing.
        def security_check():
            logger.info("security check method called.")
            return True

        self.server.add_method(security_check)

        # The 'send_request' method of this test class will always send the
        # server's security token. So define a special function for sending
        # requests via '_send_request' instead.
        def do_check_request(params):
            def request():
                try:
                    self.current_response = send_rpc_request(
                        self.server.url, "security_check", params, 0
                    )
                except Exception as e:
                    self.current_response = e

            return self._send_request(request)

        # Log errors for the 'rpc.methods' logger.
        log_capture = CapturingHandler()
        logger.addHandler(log_capture)
        last_length = [0]

        def next_log_msg():
            records = log_capture.records
            assert len(records) > last_length[0], "no next log message"
            last_length[0] = len(records)
            return records[len(records) - 1].msg

        try:
            # Test with no security token.
            self.assertRaises(RuntimeError, do_check_request, ())
            self.assertIn(next_log_msg(),
                          "client did not send the required "
                          "'security_token' argument")

            # Test with an invalid security token using positional and
            # keyword arguments.
            invalid_token = "NotTheTokenYou'reLookingFor"
            invalid_msg = ("Client sent a security token that did not "
                           "match the server\'s")
            self.assertRaises(RuntimeError, do_check_request,
                              [invalid_token])
            self.assertIn(next_log_msg(), invalid_msg)
            self.assertRaises(RuntimeError, do_check_request,
                              {"security_token": invalid_token})
            self.assertIn(next_log_msg(), invalid_msg)

            # Test with the correct security token.
            valid_msg = "security check method called."
            self.assertTrue(do_check_request([self.server.security_token]))
            self.assertIn(next_log_msg(), valid_msg)
            self.assertTrue(do_check_request({
                "security_token": self.server.security_token}))
            self.assertIn(next_log_msg(), valid_msg)

            # Also check using the normal send_request method that adds the
            # security token automatically.
            self.assertTrue(self.send_request("security_check", []))
            self.assertIn(next_log_msg(), valid_msg)
        finally:
            logger.removeHandler(log_capture)

    def test_list_grammars(self):
        """ Verify that the 'list_grammars' RPC method works correctly. """
        # Load a Grammar with three rules and check that the RPC returns the
        # correct data for them.
        g = Grammar("list_grammars_test")
        g.add_rule(CompoundRule(name="compound", spec="testing",
                                exported=True))
        g.add_rule(MappingRule(name="mapping", mapping={
            "command a": ActionBase(),
            "command b": ActionBase()
        }))
        g.add_rule(Rule(name="base", element=Literal("hello world"),
                        exported=False))
        g.load()

        response = self.send_request("list_grammars", [])
        expected_grammar_data = {
            "name": g.name, "enabled": True, "active": True, "rules": [
                {"name": "compound", "specs": ["testing"],
                 "exported": True, "active": True},
                {"name": "mapping", "specs": ["command a", "command b"],
                 "exported": True, "active": True},
                {"name": "base", "specs": ["hello world"],
                 "exported": False, "active": True}
            ]
        }
        # Check that the loaded grammar appears in the result. It might not
        # be the only grammar and that is acceptable because dragonfly's
        # tests can be run while user grammars are loaded.
        try:
            self.assertIn("result", response)
            self.assertIn(expected_grammar_data, response["result"])
        finally:
            g.unload()

    def test_mimic(self):
        """ Verify that the 'mimic' RPC method works correctly. """
        g = Grammar("mimic_test")
        g.add_rule(CompoundRule(name="compound", spec="testing mimicry",
                                exported=True))
        g.load()

        # Set the grammar as exclusive.
        # The sapi5shared engine apparently requires this for mimic() to
        # work, making the method kind of useless. This does not apply to
        # sapi5inproc.
        g.set_exclusiveness(True)

        response = self.send_request("mimic", ["testing mimicry"])
        try:
            self.assertIn("result", response)
            self.assertEqual(response["result"], True)
        finally:
            g.set_exclusiveness(False)
            g.unload()

    def test_speak(self):
        response = self.send_request("speak", ["testing speak"])
        self.assertIn("result", response)
        self.assertEqual(response["result"], None)

    def test_get_engine_language(self):
        """ Verify that the 'speak' RPC method works correctly. """
        response = self.send_request("get_engine_language", [])
        self.assertIn("result", response)
        self.assertEqual(response["result"], "en")

    def test_recognition_history_methods(self):
        """ Verify that the recognition history RPC methods work correctly.
        """
        # Load a grammar for testing that recognitions are saved.
        g = Grammar("history_test")
        g.add_rule(CompoundRule(name="compound", spec="test history",
                                exported=True))
        g.load()
        g.set_exclusiveness(True)
        try:
            # Test 'register_history()'.
            response = self.send_request("register_history", [])
            self.assertIn("result", response)

            # Test that the method raises an error if used when the observer
            # is already registered.
            self.assertRaises(RuntimeError, self.send_request,
                              "register_history", [])

            # Send a mimic and check that it is returned by the
            # 'get_recognition_history()' method.
            self.send_request("mimic", ["test history"])
            response = self.send_request("get_recognition_history", [])
            self.assertIn("result", response)
            self.assertListEqual(response["result"], [["test", "history"]])

            # Test 'unregister_observer()'.
            response = self.send_request("unregister_history", [])
            self.assertIn("result", response)

            # Test that the method raises an error if used when the observer
            # is not registered.
            self.assertRaises(RuntimeError, self.send_request,
                              "unregister_history", [])
        finally:
            g.set_exclusiveness(False)
            g.unload()


if __name__ == '__main__':
    # Use the "text" engine by default and disable timer manager callbacks
    # to avoid race conditions.
    get_engine("text")._timer_manager.disable()

    from dragonfly.log import setup_log
    setup_log()  # tests require sane logging levels
    unittest.main()

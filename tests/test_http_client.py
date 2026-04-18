import unittest
from unittest.mock import Mock, patch

import requests

from services.http_client import (
    HttpClient,
    RetryPolicy,
    TimeoutDefaults,
    classify_failure,
    is_retryable_exception,
    is_retryable_status,
    is_terminal_exception,
)


class HttpClientTests(unittest.TestCase):
    def test_retries_retryable_status_then_succeeds(self):
        first = Mock(status_code=503)
        second = Mock(status_code=200)
        session = Mock()
        session.request.side_effect = [first, second]
        sleep = Mock()

        client = HttpClient(session=session, sleeper=sleep)
        response = client.get("https://example.com")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.request.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    def test_uses_default_timeout_when_not_overridden(self):
        session = Mock()
        session.request.return_value = Mock(status_code=200)

        defaults = TimeoutDefaults(connect_seconds=1.5, read_seconds=7.0)
        client = HttpClient(session=session, timeout_defaults=defaults)
        client.get("https://example.com")

        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["timeout"], (1.5, 7.0))

    def test_per_request_timeout_override(self):
        session = Mock()
        session.request.return_value = Mock(status_code=200)

        client = HttpClient(session=session)
        client.get("https://example.com", timeout=2.2)

        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["timeout"], 2.2)

    def test_stops_retrying_after_max_attempts(self):
        session = Mock()
        session.request.return_value = Mock(status_code=503)
        sleep = Mock()

        client = HttpClient(
            session=session,
            sleeper=sleep,
            retry_policy=RetryPolicy(max_attempts=2, backoff_base_seconds=0.0, jitter_seconds=0.0),
        )
        response = client.get("https://example.com")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(session.request.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    @patch("services.http_client.random.uniform", return_value=0.0)
    def test_retries_on_connection_errors(self, _):
        session = Mock()
        session.request.side_effect = [requests.ConnectionError("transient"), Mock(status_code=200)]
        sleep = Mock()

        client = HttpClient(session=session, sleeper=sleep)
        response = client.get("https://example.com")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.request.call_count, 2)
        self.assertEqual(sleep.call_count, 1)


class ClassificationHelperTests(unittest.TestCase):
    def test_retryable_status_and_exception_helpers(self):
        self.assertTrue(is_retryable_status(503))
        self.assertFalse(is_retryable_status(400))
        self.assertTrue(is_retryable_exception(requests.Timeout("t")))
        self.assertFalse(is_retryable_exception(requests.HTTPError("boom")))

    def test_terminal_exception_helper(self):
        self.assertTrue(is_terminal_exception(requests.HTTPError("boom")))
        self.assertFalse(is_terminal_exception(requests.Timeout("slow")))
        self.assertTrue(is_terminal_exception(ValueError("x")))

    def test_classify_failure(self):
        self.assertEqual(classify_failure(status_code=429), "retryable")
        self.assertEqual(classify_failure(status_code=404), "terminal")
        self.assertEqual(classify_failure(exc=requests.ConnectionError("c")), "retryable")
        self.assertEqual(classify_failure(exc=requests.HTTPError("h")), "terminal")
        self.assertEqual(classify_failure(), "unknown")


if __name__ == "__main__":
    unittest.main()

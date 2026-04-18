"""Reusable HTTP client with retry, timeout defaults, and error classification helpers."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

import requests


DEFAULT_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    """Controls retry behavior for transient HTTP failures."""

    max_attempts: int = 3
    backoff_base_seconds: float = 0.25
    backoff_multiplier: float = 2.0
    jitter_seconds: float = 0.1
    max_backoff_seconds: float = 5.0
    retryable_status_codes: frozenset[int] = DEFAULT_RETRYABLE_STATUS_CODES

    def normalized(self) -> "RetryPolicy":
        """Return a validated copy with bounded values."""
        return RetryPolicy(
            max_attempts=max(1, int(self.max_attempts)),
            backoff_base_seconds=max(0.0, float(self.backoff_base_seconds)),
            backoff_multiplier=max(1.0, float(self.backoff_multiplier)),
            jitter_seconds=max(0.0, float(self.jitter_seconds)),
            max_backoff_seconds=max(0.0, float(self.max_backoff_seconds)),
            retryable_status_codes=frozenset(self.retryable_status_codes),
        )


@dataclass(frozen=True)
class TimeoutDefaults:
    """Default timeout values for outgoing requests."""

    connect_seconds: float = 3.05
    read_seconds: float = 10.0

    def as_tuple(self) -> tuple[float, float]:
        return (self.connect_seconds, self.read_seconds)


class HttpClient:
    """Thin wrapper around requests.Session with retry and timeout behavior."""

    def __init__(
        self,
        *,
        retry_policy: RetryPolicy | None = None,
        timeout_defaults: TimeoutDefaults | None = None,
        session: requests.Session | None = None,
        sleeper: Any = time.sleep,
    ) -> None:
        self.retry_policy = (retry_policy or RetryPolicy()).normalized()
        self.timeout_defaults = timeout_defaults or TimeoutDefaults()
        self.session = session or requests.Session()
        self._sleep = sleeper

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float | tuple[float, float] | None = None,
        retry_policy: RetryPolicy | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send an HTTP request with retries for transient failures.

        `timeout` can override the default for this request (single float or
        `(connect, read)` tuple).
        """
        policy = (retry_policy or self.retry_policy).normalized()
        resolved_timeout = timeout if timeout is not None else self.timeout_defaults.as_tuple()

        attempt = 1
        while True:
            try:
                response = self.session.request(method=method, url=url, timeout=resolved_timeout, **kwargs)
            except requests.RequestException as exc:
                if attempt >= policy.max_attempts or not is_retryable_exception(exc):
                    raise
                self._sleep(self._compute_delay(attempt, policy))
                attempt += 1
                continue

            if attempt < policy.max_attempts and is_retryable_status(response.status_code, policy.retryable_status_codes):
                self._sleep(self._compute_delay(attempt, policy))
                attempt += 1
                continue

            return response

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)

    @staticmethod
    def _compute_delay(attempt: int, policy: RetryPolicy) -> float:
        exponent = max(0, attempt - 1)
        base = policy.backoff_base_seconds * (policy.backoff_multiplier**exponent)
        bounded = min(base, policy.max_backoff_seconds)
        return bounded + random.uniform(0.0, policy.jitter_seconds)


def is_retryable_status(status_code: int, retryable_status_codes: frozenset[int] | None = None) -> bool:
    """Return True when an HTTP status code indicates a transient error."""
    retryable = retryable_status_codes or DEFAULT_RETRYABLE_STATUS_CODES
    return status_code in retryable


def is_retryable_exception(exc: BaseException) -> bool:
    """Return True when a raised requests exception is generally transient."""
    return isinstance(
        exc,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError,
            requests.exceptions.ChunkedEncodingError,
        ),
    )


def is_terminal_exception(exc: BaseException) -> bool:
    """Return True when an exception should not be retried."""
    if not isinstance(exc, requests.RequestException):
        return True

    return not is_retryable_exception(exc)


def classify_failure(status_code: int | None = None, exc: BaseException | None = None) -> str:
    """Classify an HTTP failure as `retryable`, `terminal`, or `unknown`."""
    if status_code is not None:
        return "retryable" if is_retryable_status(status_code) else "terminal"
    if exc is not None:
        return "retryable" if is_retryable_exception(exc) else "terminal"
    return "unknown"

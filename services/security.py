"""Utilities for redacting sensitive values from diagnostic payloads.

This module intentionally does not mutate existing logging statements. It provides
helpers that callers can opt into when preparing structured data for logs,
exceptions, metrics dimensions, or debug snapshots.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

# Field-name fragments that usually indicate secret material.
_SENSITIVE_FIELD_FRAGMENTS = (
    "password",
    "passwd",
    "passphrase",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "client_secret",
    "authorization",
    "auth",
    "cookie",
    "session",
    "credential",
    "signature",
)

# Patterns for secret-like content embedded in arbitrary strings.
_SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(bearer\s+)[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,;]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s,;]+"),
    re.compile(r"(?i)(password\s*[=:]\s*)[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
)

REDACTION_TOKEN = "[REDACTED]"


def is_sensitive_field_name(field_name: str) -> bool:
    """Return True when the field name likely stores a secret/token/password."""
    normalized = field_name.strip().lower().replace("-", "_")
    return any(fragment in normalized for fragment in _SENSITIVE_FIELD_FRAGMENTS)


def redact_value(value: Any, replacement: str = REDACTION_TOKEN) -> str:
    """Return a fixed redaction marker, regardless of input type/value."""
    _ = value
    return replacement


def scrub_string(text: str, replacement: str = REDACTION_TOKEN, max_length: int = 1000) -> str:
    """Redact secret-looking segments from free-form text.

    Args:
        text: Raw text that may include embedded credentials.
        replacement: Redaction token inserted when a match is found.
        max_length: Maximum resulting length to keep snapshots compact.
    """
    sanitized = text
    for pattern in _SECRET_VALUE_PATTERNS:
        if pattern.pattern.startswith("\\bsk-"):
            sanitized = pattern.sub(replacement, sanitized)
        else:
            sanitized = pattern.sub(rf"\1{replacement}", sanitized)

    if len(sanitized) > max_length:
        sanitized = f"{sanitized[: max_length - 3]}..."
    return sanitized


def scrub_dict(payload: Mapping[str, Any], replacement: str = REDACTION_TOKEN, max_depth: int = 8) -> dict[str, Any]:
    """Return a recursively scrubbed copy of a structured payload."""
    return _scrub_value(payload, replacement=replacement, max_depth=max_depth, depth=0)


def safe_diagnostic_snapshot(
    payload: Any,
    *,
    max_depth: int = 6,
    max_items: int = 30,
    max_string_length: int = 300,
) -> Any:
    """Build a compact, redacted, serialization-friendly snapshot.

    The output is intended for diagnostics and may truncate deep or large
    structures to keep logs bounded.
    """
    return _snapshot_value(
        payload,
        depth=0,
        max_depth=max_depth,
        max_items=max_items,
        max_string_length=max_string_length,
    )


def _scrub_value(value: Any, *, replacement: str, max_depth: int, depth: int) -> Any:
    if depth >= max_depth:
        return "[TRUNCATED_DEPTH]"

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, inner_value in value.items():
            key_str = str(key)
            if is_sensitive_field_name(key_str):
                result[key_str] = replacement
            else:
                result[key_str] = _scrub_value(
                    inner_value,
                    replacement=replacement,
                    max_depth=max_depth,
                    depth=depth + 1,
                )
        return result

    if isinstance(value, str):
        return scrub_string(value, replacement=replacement)

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _scrub_value(item, replacement=replacement, max_depth=max_depth, depth=depth + 1)
            for item in value
        ]

    if isinstance(value, (bytes, bytearray)):
        return replacement

    return value


def _snapshot_value(
    value: Any,
    *,
    depth: int,
    max_depth: int,
    max_items: int,
    max_string_length: int,
) -> Any:
    if depth >= max_depth:
        return "[TRUNCATED_DEPTH]"

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        count = 0
        for key, inner in value.items():
            if count >= max_items:
                out["__truncated_items__"] = f"+{len(value) - max_items}"
                break

            key_str = str(key)
            if is_sensitive_field_name(key_str):
                out[key_str] = REDACTION_TOKEN
            else:
                out[key_str] = _snapshot_value(
                    inner,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                    max_string_length=max_string_length,
                )
            count += 1
        return out

    if isinstance(value, str):
        return scrub_string(value, max_length=max_string_length)

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items = []
        for idx, item in enumerate(value):
            if idx >= max_items:
                items.append(f"[+{len(value) - max_items} more]")
                break
            items.append(
                _snapshot_value(
                    item,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                    max_string_length=max_string_length,
                )
            )
        return items

    if isinstance(value, (bytes, bytearray)):
        return REDACTION_TOKEN

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    # Fallback for custom types.
    return scrub_string(repr(value), max_length=max_string_length)

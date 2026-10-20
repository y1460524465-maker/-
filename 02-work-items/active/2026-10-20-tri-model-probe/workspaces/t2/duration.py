"""Parse duration strings into exact integer milliseconds.

Grammar: segments of ``<ASCII decimal integer><unit>`` joined without any
whitespace, where units appear at most once each and strictly in the order
``d``, ``h``, ``m``, ``s``, ``ms`` (intermediate units may be skipped).
Every segment value must be positive; the only zero accepted is the whole
input ``"0s"``.

Digits are accumulated by hand instead of ``int(text)`` so that results stay
exact arbitrary-precision integers even when they exceed the interpreter's
``str``-to-``int`` conversion limit (CPython 3.11+ defaults to 4300 digits).
"""

import re

_MS_PER_UNIT = {
    "d": 86_400_000,
    "h": 3_600_000,
    "m": 60_000,
    "s": 1_000,
    "ms": 1,
}

_DURATION = re.compile(
    r"(?:(?P<d>[0-9]+)d)?"
    r"(?:(?P<h>[0-9]+)h)?"
    r"(?:(?P<m>[0-9]+)m)?"
    r"(?:(?P<s>[0-9]+)s)?"
    r"(?:(?P<ms>[0-9]+)ms)?"
)


def _exact_int(digits: str) -> int:
    """Convert ASCII digits to an int without the str-to-int digit limit."""
    value = 0
    for char in digits:
        value = value * 10 + (ord(char) - 48)
    return value


def parse_duration(value: str) -> int:
    """Return the exact number of milliseconds described by ``value``.

    Raises:
        ValueError: if ``value`` does not match the grammar above.
    """
    if value == "0s":
        return 0
    if not value:
        raise ValueError("duration must not be empty")

    match = _DURATION.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid duration: {value!r}")

    total = 0
    for unit, factor in _MS_PER_UNIT.items():
        digits = match.group(unit)
        if digits is None:
            continue
        amount = _exact_int(digits)
        if amount == 0:
            raise ValueError(f"invalid duration: {value!r}")
        total += amount * factor
    return total

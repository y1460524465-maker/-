"""Tag normalization."""

import re

_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_tag(value: str) -> str:
    """Normalize a tag to lowercase words joined by single ASCII hyphens.

    Leading and trailing whitespace is removed, consecutive whitespace is
    collapsed to one ``-``, and leading/trailing ``-`` are removed.  Other
    characters, including Unicode letters and punctuation, are preserved.

    Raises:
        ValueError: if ``value`` is empty or contains only whitespace.
    """
    tag = value.strip()
    if not tag:
        raise ValueError("tag must not be empty or whitespace-only")

    tag = tag.lower()
    tag = _WHITESPACE_RUN.sub("-", tag)
    return tag.strip("-")

"""Slug normalisation for workspace directory names."""

from __future__ import annotations

import re

_MAX_LENGTH = 64


def slugify(value: str) -> str:
    """Normalise a user-provided string into a URL-safe slug.

    Rules:
    - Lowercase
    - Spaces and underscores replaced with hyphens
    - Non-alphanumeric, non-hyphen characters stripped
    - Consecutive hyphens collapsed
    - Leading/trailing hyphens stripped
    - Truncated to 64 characters; trailing hyphens removed after truncation

    Args:
        value: Raw user input.

    Returns:
        Normalised slug string.

    Raises:
        ValueError: If the resulting slug is empty.
    """
    slug = value.lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    slug = slug[:_MAX_LENGTH].rstrip("-")
    if not slug:
        raise ValueError(f"Slug is empty after normalisation: {value!r}")
    return slug

"""Slug normalization for workspace IDs.

Rules (applied in order):
1. Unicode → ASCII via NFKD decomposition, stripping non-ASCII.
2. Lowercase.
3. Non-alphanumeric characters → '-'.
4. Consecutive '-' collapsed to single '-'.
5. Leading/trailing '-' stripped.
6. Truncated to 100 characters at a word boundary (last '-' at or before position 100).
7. Empty result raises ValueError.
"""

from __future__ import annotations

import unicodedata


def slugify(text: str) -> str:
    """Normalize *text* into a valid workspace slug.

    Args:
        text: Raw input string (task description, etc.).

    Returns:
        A normalized slug string.

    Raises:
        ValueError: If normalization produces an empty string.
    """
    # Step 1: Unicode → ASCII
    normalized = unicodedata.normalize("NFKD", text)
    ascii_bytes = normalized.encode("ascii", "ignore")
    result = ascii_bytes.decode("ascii")

    # Step 2: Lowercase
    result = result.lower()

    # Step 3: Non-alphanumeric → '-'
    chars = []
    for ch in result:
        if ch.isalnum():
            chars.append(ch)
        else:
            chars.append("-")
    result = "".join(chars)

    # Step 4: Collapse consecutive '-'
    while "--" in result:
        result = result.replace("--", "-")

    # Step 5: Strip leading/trailing '-'
    result = result.strip("-")

    # Step 6: Truncate to 100 chars at a word boundary
    if len(result) > 100:
        truncated = result[:100]
        # Find last '-' at or before position 100
        last_sep = truncated.rfind("-")
        if last_sep > 0:
            result = truncated[:last_sep]
        else:
            result = truncated
        result = result.strip("-")

    # Step 7: Raise on empty
    if not result:
        raise ValueError(f"Slug normalization of {text!r} produced an empty string.")

    return result

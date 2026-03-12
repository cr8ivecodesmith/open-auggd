"""Unit tests for workspace/slugify.py."""

import importlib

import pytest

_mod = importlib.import_module("open_auggd.workspace.slugify")
slugify = _mod.slugify


# ---------------------------------------------------------------------------
# basic normalisation
# ---------------------------------------------------------------------------


def test_lowercase():
    assert slugify("Hello World") == "hello-world"


def test_spaces_become_hyphens():
    assert slugify("add user authentication") == "add-user-authentication"


def test_underscores_become_hyphens():
    assert slugify("add_user_authentication") == "add-user-authentication"


def test_already_clean_slug_unchanged():
    assert slugify("add-user-auth") == "add-user-auth"


def test_mixed_separators_collapsed():
    assert slugify("add  user__auth") == "add-user-auth"


def test_special_chars_stripped():
    assert slugify("add user (auth)!") == "add-user-auth"


def test_leading_trailing_hyphens_stripped():
    assert slugify("--add-user--") == "add-user"


def test_numbers_preserved():
    assert slugify("phase 3 spec") == "phase-3-spec"


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------


def test_empty_string_raises():
    with pytest.raises(ValueError, match="empty"):
        slugify("")


def test_all_special_chars_raises():
    with pytest.raises(ValueError, match="empty"):
        slugify("!!!@@@###")


def test_max_length_truncated():
    long_input = "a" * 200
    result = slugify(long_input)
    assert len(result) <= 64


def test_max_length_does_not_end_with_hyphen():
    # Build something that would end mid-word at exactly 64 chars
    long_input = ("word-" * 20)[:200]
    result = slugify(long_input)
    assert not result.endswith("-")

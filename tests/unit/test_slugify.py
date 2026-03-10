"""Unit tests for workspace slug normalization."""

import pytest

from open_auggd.workspace.slugify import slugify


class TestSlugify:
    """Tests for the slugify function."""

    def test_basic_ascii(self):
        assert slugify("Add user authentication") == "add-user-authentication"

    def test_lowercase(self):
        assert slugify("Fix Auth Middleware") == "fix-auth-middleware"

    def test_non_alphanumeric_to_dash(self):
        assert slugify("hello, world!") == "hello-world"

    def test_consecutive_dashes_collapsed(self):
        assert slugify("foo   bar") == "foo-bar"

    def test_leading_trailing_stripped(self):
        assert slugify("  -hello-  ") == "hello"

    def test_unicode_to_ascii(self):
        # é → e after NFKD decomposition
        assert slugify("café au lait") == "cafe-au-lait"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            slugify("")

    def test_non_ascii_only_raises(self):
        # All non-ASCII, strips to empty
        with pytest.raises(ValueError):
            slugify("中文")

    def test_truncation_at_100(self):
        long_input = "a-" * 60  # 120 chars
        result = slugify(long_input)
        assert len(result) <= 100

    def test_truncation_at_word_boundary(self):
        # Construct a slug that's exactly 105 chars: 'word' segments separated by '-'
        slug = "-".join(["word"] * 21)  # 4*21 + 20 = 104 chars
        result = slugify(slug)
        assert len(result) <= 100
        assert not result.endswith("-")

    def test_numbers_preserved(self):
        assert slugify("fix bug 42") == "fix-bug-42"

    def test_already_slug(self):
        assert slugify("add-user-auth") == "add-user-auth"

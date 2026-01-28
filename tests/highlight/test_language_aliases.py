"""Tests for language alias resolution."""

from codepicture.highlight import EXTRA_ALIASES, resolve_language_alias


class TestExtraAliases:
    """Tests for EXTRA_ALIASES dictionary."""

    def test_contains_yml_to_yaml_mapping(self) -> None:
        """Verify yml->yaml mapping exists."""
        assert "yml" in EXTRA_ALIASES
        assert EXTRA_ALIASES["yml"] == "yaml"


class TestResolveLanguageAlias:
    """Tests for resolve_language_alias function."""

    def test_resolves_known_alias(self) -> None:
        """Verify known alias resolves to canonical name."""
        assert resolve_language_alias("yml") == "yaml"

    def test_unknown_alias_passes_through(self) -> None:
        """Verify unknown language passes through unchanged."""
        assert resolve_language_alias("python") == "python"
        assert resolve_language_alias("rust") == "rust"

    def test_case_insensitive(self) -> None:
        """Verify alias resolution is case-insensitive."""
        assert resolve_language_alias("YML") == "yaml"
        assert resolve_language_alias("Yml") == "yaml"

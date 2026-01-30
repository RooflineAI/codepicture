"""Tests for MLIR lexer."""

import pathlib

import pytest
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
)

from codepicture.highlight.mlir_lexer import MlirLexer
from codepicture.highlight import PygmentsHighlighter


class TestMlirLexerMetadata:
    """Test lexer registration and metadata."""

    def test_lexer_name(self):
        lexer = MlirLexer()
        assert lexer.name == "MLIR"

    def test_lexer_aliases(self):
        lexer = MlirLexer()
        assert "mlir" in lexer.aliases

    def test_lexer_filenames(self):
        lexer = MlirLexer()
        assert "*.mlir" in lexer.filenames


class TestMlirLexerTokens:
    """Test token recognition for MLIR constructs."""

    @pytest.fixture
    def lexer(self):
        return MlirLexer()

    def _get_tokens(self, lexer, code: str) -> list[tuple]:
        """Helper to get tokens without trailing newline token."""
        tokens = list(lexer.get_tokens(code))
        # Remove trailing whitespace token
        if tokens and tokens[-1][0] in (Text.Whitespace, Text):
            tokens = tokens[:-1]
        return tokens

    def test_single_line_comment(self, lexer):
        tokens = self._get_tokens(lexer, "// this is a comment")
        assert any(t[0] == Comment.Single for t in tokens)

    def test_ssa_value(self, lexer):
        tokens = self._get_tokens(lexer, "%result")
        assert any(t[0] == Name.Variable and "%result" in t[1] for t in tokens)

    def test_ssa_value_numbered(self, lexer):
        tokens = self._get_tokens(lexer, "%0")
        assert any(t[0] == Name.Variable for t in tokens)

    def test_ssa_value_with_special_chars(self, lexer):
        tokens = self._get_tokens(lexer, "%arg0:1")
        assert any(t[0] == Name.Variable for t in tokens)

    def test_block_label(self, lexer):
        tokens = self._get_tokens(lexer, "^bb0")
        assert any(t[0] == Name.Label for t in tokens)

    def test_function_reference(self, lexer):
        tokens = self._get_tokens(lexer, "@main")
        assert any(t[0] == Name.Function for t in tokens)

    def test_quoted_function_reference(self, lexer):
        tokens = self._get_tokens(lexer, '@"my.function"')
        assert any(t[0] == Name.Function for t in tokens)

    def test_attribute_alias(self, lexer):
        tokens = self._get_tokens(lexer, "#map0")
        assert any(t[0] == Name.Constant for t in tokens)

    def test_type_alias(self, lexer):
        tokens = self._get_tokens(lexer, "!my_type")
        assert any(t[0] == Keyword.Type for t in tokens)

    def test_builtin_type_index(self, lexer):
        tokens = self._get_tokens(lexer, "index")
        assert any(t[0] == Keyword.Type for t in tokens)

    def test_builtin_type_float(self, lexer):
        for ftype in ["f16", "f32", "f64"]:
            tokens = self._get_tokens(lexer, ftype)
            assert any(
                t[0] == Keyword.Type for t in tokens
            ), f"{ftype} should be Keyword.Type"

    def test_builtin_type_integer(self, lexer):
        for itype in ["i8", "i32", "i64", "si32", "ui64"]:
            tokens = self._get_tokens(lexer, itype)
            assert any(
                t[0] == Keyword.Type for t in tokens
            ), f"{itype} should be Keyword.Type"

    def test_container_type_memref(self, lexer):
        tokens = self._get_tokens(lexer, "memref")
        assert any(t[0] == Keyword.Type for t in tokens)

    def test_container_type_tensor(self, lexer):
        tokens = self._get_tokens(lexer, "tensor")
        assert any(t[0] == Keyword.Type for t in tokens)

    def test_operation_dialect_format(self, lexer):
        tokens = self._get_tokens(lexer, "arith.addf")
        assert any(t[0] == Name.Builtin for t in tokens)

    def test_operation_with_dots(self, lexer):
        tokens = self._get_tokens(lexer, "llvm.mlir.constant")
        assert any(t[0] == Name.Builtin for t in tokens)

    def test_reserved_keyword_func(self, lexer):
        tokens = self._get_tokens(lexer, "func")
        assert any(t[0] == Keyword.Reserved for t in tokens)

    def test_reserved_keyword_module(self, lexer):
        tokens = self._get_tokens(lexer, "module")
        assert any(t[0] == Keyword.Reserved for t in tokens)

    def test_boolean_true(self, lexer):
        tokens = self._get_tokens(lexer, "true")
        assert any(t[0] == Keyword.Constant for t in tokens)

    def test_boolean_false(self, lexer):
        tokens = self._get_tokens(lexer, "false")
        assert any(t[0] == Keyword.Constant for t in tokens)

    def test_affine_operator(self, lexer):
        tokens = self._get_tokens(lexer, "floordiv")
        assert any(t[0] == Operator.Word for t in tokens)

    def test_hex_number(self, lexer):
        tokens = self._get_tokens(lexer, "0xDEADBEEF")
        assert any(t[0] == Number.Hex for t in tokens)

    def test_float_number(self, lexer):
        tokens = self._get_tokens(lexer, "3.14159")
        assert any(t[0] == Number.Float for t in tokens)

    def test_float_number_scientific(self, lexer):
        tokens = self._get_tokens(lexer, "1.0e-10")
        assert any(t[0] == Number.Float for t in tokens)

    def test_integer_number(self, lexer):
        tokens = self._get_tokens(lexer, "42")
        assert any(t[0] == Number.Integer for t in tokens)

    def test_string_simple(self, lexer):
        tokens = self._get_tokens(lexer, '"hello"')
        assert any(t[0] == String.Double for t in tokens)

    def test_string_with_escape(self, lexer):
        tokens = self._get_tokens(lexer, '"hello\\nworld"')
        assert any(t[0] == String.Escape for t in tokens)

    def test_arrow_operator(self, lexer):
        tokens = self._get_tokens(lexer, "->")
        assert any(t[0] == Punctuation for t in tokens)

    def test_punctuation_braces(self, lexer):
        tokens = self._get_tokens(lexer, "{}")
        assert all(t[0] == Punctuation for t in tokens if t[1].strip())


class TestMlirLexerFallback:
    """Test graceful fallback for unknown constructs."""

    @pytest.fixture
    def lexer(self):
        return MlirLexer()

    def test_unknown_identifier(self, lexer):
        """Unknown identifiers should not crash the lexer."""
        tokens = list(lexer.get_tokens("unknown_thing_here"))
        assert len(tokens) > 0

    def test_mixed_known_unknown(self, lexer):
        """Mixed known and unknown tokens should all be tokenized."""
        code = "%value = unknown_dialect.op %arg : custom_type"
        tokens = list(lexer.get_tokens(code))
        assert any(t[0] == Name.Variable for t in tokens)

    def test_empty_input(self, lexer):
        """Empty input should produce no meaningful tokens."""
        tokens = list(lexer.get_tokens(""))
        # Should not crash; may produce a trailing newline token
        assert isinstance(tokens, list)


class TestMlirLexerIntegration:
    """Test integration with PygmentsHighlighter."""

    @pytest.fixture
    def highlighter(self):
        return PygmentsHighlighter()

    def test_highlight_mlir_code(self, highlighter):
        code = "%0 = arith.constant 42 : i32"
        lines = highlighter.highlight(code, "mlir")
        assert len(lines) == 1
        assert len(lines[0]) > 0

    def test_detect_language_from_filename(self, highlighter):
        code = "module {}"
        detected = highlighter.detect_language(code, filename="example.mlir")
        assert detected == "mlir"

    def test_list_languages_includes_mlir(self, highlighter):
        languages = highlighter.list_languages()
        assert "mlir" in languages

    def test_highlight_multiline_mlir(self, highlighter):
        code = "module {\n  func.func @main() {\n  }\n}"
        lines = highlighter.highlight(code, "mlir")
        assert len(lines) >= 3


class TestMlirLexerFixture:
    """Test with sample fixture file."""

    @pytest.fixture
    def sample_code(self):
        fixture_path = (
            pathlib.Path(__file__).parent.parent / "fixtures" / "sample_mlir.mlir"
        )
        return fixture_path.read_text()

    def test_fixture_highlights_without_error(self, sample_code):
        lexer = MlirLexer()
        tokens = list(lexer.get_tokens(sample_code))
        assert len(tokens) > 10

    def test_fixture_has_expected_token_types(self, sample_code):
        lexer = MlirLexer()
        tokens = list(lexer.get_tokens(sample_code))
        token_types = {t[0] for t in tokens}

        assert Comment.Single in token_types
        assert Name.Function in token_types
        assert Keyword.Type in token_types
        assert Number.Integer in token_types
        assert Name.Variable in token_types
        assert Name.Builtin in token_types
        assert String.Double in token_types
        assert Punctuation in token_types

"""Custom Pygments lexer for MLIR (Multi-Level Intermediate Representation).

MLIR is a compiler infrastructure used by LLVM that provides a flexible,
extensible intermediate representation. This lexer handles core MLIR syntax
including SSA values, operations in dialect.op format, types, attributes,
and standard control flow constructs.

Registered as a Pygments entry point so that get_lexer_by_name('mlir')
and get_lexer_for_filename('*.mlir') resolve automatically.
"""

from pygments.lexer import RegexLexer, bygroups
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


class MlirLexer(RegexLexer):
    """Pygments lexer for MLIR source files."""

    name = "MLIR"
    aliases = ["mlir"]
    filenames = ["*.mlir"]
    mimetypes = ["text/x-mlir"]

    tokens = {
        "root": [
            # Comments
            (r"//.*$", Comment.Single),
            # SSA values: %name, %0, %arg.0
            (r"%[\w\.\$\:\#]+", Name.Variable),
            # Block labels: ^bb0, ^entry
            (r"\^[\w\d_$\.\-]+", Name.Label),
            # Quoted function/symbol references: @"some.name"
            (r'@"[^"]*"', Name.Function),
            # Function/symbol references: @foo, @bar_baz
            (r"@[\w+\$\-\.]+", Name.Function),
            # Attribute aliases: #map, #trait
            (r"#[\w\$\-\.]+", Name.Constant),
            # Type aliases: !my_type
            (r"![\w\$\-\.]+", Keyword.Type),
            # Built-in scalar types
            (r"\b(index|none|bf16|f16|f32|f64|f80|f128)\b", Keyword.Type),
            # Integer types: i32, si8, ui16
            (r"\b[su]?i[0-9]+\b", Keyword.Type),
            # Container types
            (r"\b(memref|tensor|vector|complex|tuple)\b", Keyword.Type),
            # Hexadecimal numbers (before dialect.op to avoid mismatches)
            (r"0x[0-9a-fA-F]+", Number.Hex),
            # Floating-point numbers (before dialect.op to avoid 3.14 matching)
            (r"[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?", Number.Float),
            # Integers
            (r"[0-9]+", Number.Integer),
            # Operations in dialect.op format: arith.constant, func.call
            (r"[a-zA-Z_][\w]*\.[\w\.\$\-]+", Name.Builtin),
            # Reserved keywords
            (
                r"\b(affine_map|affine_set|dense|opaque|sparse|func|return|module)\b",
                Keyword.Reserved,
            ),
            # Boolean and unit literals
            (r"\b(true|false|unit)\b", Keyword.Constant),
            # Affine expression operators
            (r"\b(floordiv|ceildiv|mod|symbol)\b", Operator.Word),
            # Strings
            (r'"', String.Double, "string"),
            # Arrow operator
            (r"->", Punctuation),
            # Arithmetic operators
            (r"[+\-*/]", Operator),
            # Punctuation
            (r"[()[\]<>,{}=:]", Punctuation),
            # Whitespace
            (r"\s+", Text.Whitespace),
        ],
        "string": [
            (r'\\[nt"]', String.Escape),
            (r'[^"\\]+', String.Double),
            (r'"', String.Double, "#pop"),
        ],
    }

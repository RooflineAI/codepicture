"""Custom Pygments lexer for MLIR (Multi-Level Intermediate Representation).

MLIR is a compiler infrastructure used by LLVM that provides a flexible,
extensible intermediate representation. This lexer handles core MLIR syntax
including SSA values, operations in dialect.op format, types, attributes,
and standard control flow constructs.

Registered as a Pygments entry point so that get_lexer_by_name('mlir')
and get_lexer_for_filename('*.mlir') resolve automatically.
"""

from pygments.lexer import RegexLexer
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

    _builtin_types = (
        r"index|none|bf16|f16|f32|f64|f80|f128|"
        r"[su]?i[0-9]+"
    )
    _container_types = r"memref|tensor|vector|complex|tuple"

    tokens = {
        "root": [
            # Comments
            (r"//.*$", Comment.Single),
            # Operation names may be quoted in generic MLIR syntax.
            (r'"[^"\\]*(?:\\.[^"\\]*)*"(?=\s*\()', Name.Builtin),
            # SSA values: %name, %0, %arg.0
            (r"%[\w\.\$\#]+", Name.Variable),
            # Block labels: ^bb0, ^entry
            (r"\^[\w\d_$\.\-]+", Name.Label),
            # Quoted function/symbol references: @"some.name"
            (r'@"[^"]*"', Name.Function),
            # Function/symbol references: @foo, @bar_baz
            (r"@[\w+\$\-\.]+", Name.Function),
            # Attribute aliases: #map, #trait
            (r"#[\w\$\-\.]+", Name.Tag),
            # Type aliases: !my_type
            (r"![\w\$\-\.]+", Keyword.Type),
            # Attribute keys inside dictionaries/attribute lists
            (r"[a-zA-Z_][\w\.\$\-]*(?=\s*=)", Name.Attribute),
            # Built-in scalar types
            (rf"\b({_builtin_types})\b", Keyword.Type),
            # Element types at the end of shaped types: tensor<2x?xf32>
            (rf"(?<=x)({_builtin_types})\b", Keyword.Type),
            # Integer types: i32, si8, ui16
            (r"\b[su]?i[0-9]+\b", Keyword.Type),
            # Container types and dimension separators
            (rf"\b({_container_types})\b", Keyword.Type),
            (rf"x(?=\?|[0-9]|{_builtin_types}|{_container_types})", Operator),
            # Dynamic dimensions in shaped types
            (r"\?", Number.Integer),
            # Affine dimension/symbol identifiers: d0, d1, s0
            (r"\b[ds][0-9]+\b", Name.Variable),
            # Hexadecimal numbers (before dialect.op to avoid mismatches)
            (r"0x[0-9a-fA-F]+", Number.Hex),
            # Floating-point numbers (before dialect.op to avoid 3.14 matching)
            (r"[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?", Number.Float),
            # Integers
            (r"[0-9]+", Number.Integer),
            # Operations in dialect.op format: arith.constant, func.call
            (r"[a-zA-Z_][\w\$-]*\.[\w\.\$\-]+", Name.Builtin),
            # Reserved keywords
            (
                r"\b(affine_map|affine_set|dense|opaque|sparse|func|return|module)\b",
                Keyword.Reserved,
            ),
            # Common MLIR region/operation modifiers and linalg operands
            (
                r"\b(attributes|ins|outs|on|to|loc|sym_name|visibility)\b",
                Keyword.Namespace,
            ),
            (r"\b(public|private|nested)\b", Keyword.Declaration),
            # Boolean and unit literals
            (r"\b(true|false|unit)\b", Keyword.Constant),
            # Affine expression operators
            (r"\b(floordiv|ceildiv|mod|symbol)\b", Operator.Word),
            # Ellipsis (variadic argument marker)
            (r"\.\.\.", Punctuation),
            # General identifiers (catch-all for bare words)
            (r"[a-zA-Z_][\w]*", Name),
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

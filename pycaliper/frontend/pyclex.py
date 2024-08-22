"""
    PyCaliper

    Author: Adwait Godbole, UC Berkeley

    File: frontend/pyclex.py

    Lexer definitions based on PLY Lex
"""

from ply import lex
from ply.lex import TOKEN

# Keywords
reserved = {
    "begin": "KW_begin",
    # "bit": "KW_bit",
    # "byte": "KW_byte",
    "end": "KW_end",
    "endmodule": "KW_endmodule",
    "endstruct": "KW_endstruct",
    "foreach": "KW_foreach",
    "if": "KW_if",
    # "inside": "KW_inside",
    "input": "KW_input",
    # "int": "KW_int",
    # "integer": "KW_integer",
    "logic": "KW_logic",
    # "longint": "KW_longint",
    "module": "KW_module",
    # "null": "KW_null",
    "output": "KW_output",
    "parameter": "KW_parameter",
    # "real": "KW_real",
    # "realtime": "KW_realtime",
    # "reg": "KW_reg",
    # "shortint": "KW_shortint",
    # "shortreal": "KW_shortreal",
    "struct": "KW_struct",
    "this": "KW_this",
    # "time": "KW_time",
    # "with": "KW_with",
    # PYC tokens
    "def": "KW_def",
    "invariant": "KW_invariant",
    "submodule": "KW_submodule",
    "state": "KW_state",
    "spec": "KW_spec",
    "endspec": "KW_endspec",
}


tokens = [
    # numerals
    "Num",
    # identifiers
    "Ident",
    # string literals
    # "String",
    # White space
    # "WhiteSpace",
    # Comments
    "LineComment",
    # Symbols
    "BracketL",
    "BracketR",
    "ParenL",
    "ParenR",
    "Comma",
    "Semi",
    "Dot",
    # "BraceL",
    # "BraceR",
    "Equals",
    "Colon",
    "Question",
    # "Dollar",
    "Not",
    "Tilde"
    # , "NotOr"
    # , "NotAnd"
    # , "XorNot"
    # , "PlusColon"
    # , "MinusColon"
    # Operators
    ,
    "Plus",
    "Minus",
    "Star",
    "Divide",
    # "Power",
    "Mod",
    # "Equality",
    # "Inequality",
    # "CaseEquality",
    # "CaseInequality",
    # "WildcardEquality",
    # "WildcardInequality",
    "LessThan",
    # "LessThanEqual",
    "GreaterThan",
    # "GreaterThanEqual",
    # "LogicalAnd",
    # "LogicalOr",
    "Amp",
    "Bar",
    "Carat"
    # "BinaryXnor",
    # "LogicalImplication",
    # "LogicalEquivalence",
    # "LogicalShiftLeft",
    # "LogicalShiftRight",
    # "ArithmeticShiftLeft",
    # "ArithmeticShiftRight",
] + list(reserved.values())


# Define the tokens

# @non_zero_number = $non_zero_digit (_ | $decimal_digit)*
non_zero_number = r"[1-9](_|[0-9])*"
# @unsigned_number = $decimal_digit ( _ | $decimal_digit )*
unsigned_number = r"[0-9](_|[0-9])*"
# @binary_value    = $binary_digit ( _ | $binary_digit )*
binary_value = r"[xXzZ0-1](_|[xXzZ0-1])*"
# @octal_value     = $octal_digit ( _ | $octal_digit )*
octal_value = r"[xXzZ0-7](_|[xXzZ0-7])*"
# @hex_value       = $hex_digit ( _ | $hex_digit )*
hex_value = r"[xXzZ0-9A-Fa-f](_|[xXzZ0-9A-Fa-f])*"

# @size = @non_zero_number
size = non_zero_number

# Bases
decimal_base = r"\'[sS]?[dD]"
binary_base = r"\'[sS]?[bB]"
octal_base = r"\'[sS]?[oO]"
hex_base = r"\'[sS]?[hH]"


# @decimal_number = @unsigned_number | @size? decimal_base unsigned_number
decimal_number = unsigned_number + r"|" + size + r"?" + decimal_base + unsigned_number
# @binary_number  = @size? @binary_base @binary_value
binary_number = size + r"?" + binary_base + binary_value
# @octal_number   = @size? @octal_base @octal_value
octal_number = size + r"?" + octal_base + octal_value
# @hex_number     = @size? @hex_base @hex_value
hex_number = size + r"?" + hex_base + hex_value
# @unbased_unsized_literal  = \' [0 1 x X z Z]
unbased_unsized_literal = r"\'[01xXzZ]"

# @integral_number = @decimal_number | @octal_number | @binary_number | @hex_number
integral_number = (
    decimal_number
    + r"|"
    + octal_number
    + r"|"
    + binary_number
    + r"|"
    + hex_number
    + r"|"
    + unbased_unsized_literal
)

# @simple_identifier = [ a-zA-Z_ ] [ a-zA-Z0-9_\$ ]*
# simple_identifier = r"[a-zA-Z_][a-zA-Z0-9_\$]*"
# @system_tf_identifier = \$ [ a-zA-Z0-9_\$ ]*
# system_tf_identifier = r"\$[a-zA-Z0-9_\$]*"
any_identifier = r"[a-zA-Z_][a-zA-Z0-9_\$]*" + r"|" + r"\$[a-zA-Z0-9_\$]*"

# Symbols
t_BracketL = r"\["
t_BracketR = r"\]"
t_ParenL = r"\("
t_ParenR = r"\)"
t_Comma = r","
t_Semi = r";"
t_Dot = r"\."
# t_BraceL = r"\{"
# t_BraceR = r"\}"
t_Equals = r"="
t_Colon = r":"
t_Question = r"\?"
# t_Dollar = r"\$"
t_Not = r"!"
t_Tilde = r"~"
# t_NotOr = r"~\|"
# t_NotAnd = r"~&"
# t_XorNot = r"\^~"
# t_PlusColon = r"\+:"
# t_MinusColon = r"\-:"

# Operators
t_Plus = r"\+"
t_Minus = r"\-"
t_Star = r"\*"
t_Divide = r"/"
# t_Power = r"\*\*"
t_Mod = r"%"
# t_Equality = r"=="
# t_Inequality = r"!="
# t_CaseEquality = r"==="
# t_CaseInequality = r"!=="
# t_WildcardEquality = r"==?"
# t_WildcardInequality = r"!=?"
t_LessThan = r"<"
# t_LessThanEqual = r"<="
t_GreaterThan = r">"
# t_GreaterThanEqual = r">="
# t_LogicalAnd = r"&&"
# t_LogicalOr = r"\|\|"
t_Amp = r"&"
t_Bar = r"\|"
t_Carat = r"\^"
# t_BinaryXnor = r"\^~"
# t_LogicalImplication = r"->"
# t_LogicalEquivalence = r"<->"
# t_LogicalShiftLeft = r"<<"
# t_LogicalShiftRight = r">>"
# t_ArithmeticShiftLeft = r"<<<"
# t_ArithmeticShiftRight = r">>>"


@TOKEN(any_identifier)
def t_Ident(t):
    t.type = reserved.get(t.value, "Ident")  # Check for reserved words
    return t


@TOKEN(integral_number)
def t_Num(t):
    return t


def t_LineComment(t):
    r"//.*"
    pass


# A string containing ignored characters (spaces and tabs)
t_ignore = " \t"

# Define a rule so we can track line numbers
def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()

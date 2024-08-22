"""
    PyCaliper

    Author: Adwait Godbole, UC Berkeley

    File: frontend/pycparse.py

    Parser based on PLY Yacc
"""

import logging

from ply import yacc

from pycaliper.frontend.pyclex import tokens
from pycaliper.frontend.pycast import *


logger = logging.getLogger(__name__)

# ================================================
#   Helpers: empty, and lists
# ================================================
def p_empty(p):
    "empty :"
    pass


def p_expr_list_p_1(p):
    """expr_list_p   : expression"""
    p[0] = [p[1]]


def p_expr_list_p_2(p):
    """expr_list_p   : expression Comma expr_list_p"""
    p[0] = [p[1]] + p[3]


def p_expr_list_1(p):
    """expr_list   : empty"""
    p[0] = []


def p_expr_list_2(p):
    """expr_list   : expr_list_p"""
    p[0] = p[1]


def p_primary1_list_p_1(p):
    """primary1_list_p   : primary1"""
    p[0] = [p[1]]


def p_primary1_list_p_2(p):
    """primary1_list_p   : primary1 Comma primary1_list_p"""
    p[0] = [p[1]] + p[3]


def p_caliper_statement_list_p_1(p):
    """caliper_statement_list_p   : caliper_statement"""
    p[0] = [p[1]]


def p_caliper_statement_list_p_2(p):
    """caliper_statement_list_p   : caliper_statement caliper_statement_list_p"""
    p[0] = [p[1]] + p[2]


def p_caliper_statement_list_1(p):
    """caliper_statement_list   : empty"""
    p[0] = []


def p_caliper_statement_list_2(p):
    """caliper_statement_list   : caliper_statement_list_p"""
    p[0] = p[1]


def p_caliper_mod_stmt_list_1(p):
    """caliper_mod_stmt_list : caliper_mod_stmt"""
    p[0] = [p[1]]


def p_caliper_mod_stmt_list_2(p):
    """caliper_mod_stmt_list : caliper_mod_stmt caliper_mod_stmt_list"""
    p[0] = [p[1]] + p[2]


# ================================================
#   Operators
# ================================================
def p_PlusColon(p):
    """PlusColon : Plus Colon"""
    p[0] = "+:"


def p_MinusColon(p):
    """MinusColon : Minus Colon"""
    p[0] = "-:"


def p_Power(p):
    """Power : Star Star"""
    p[0] = "**"


def p_Equality(p):
    """Equality : Equals Equals"""
    p[0] = "=="


def p_Inequality(p):
    """Inequality : Not Equals"""
    p[0] = "!="


def p_CaseEquality(p):
    """CaseEquality : Equals Equals Equals"""
    p[0] = "==="


def p_CaseInequality(p):
    """CaseInequality : Not Equals Equals"""
    p[0] = "!=="


def p_WildcardEquality(p):
    """WildcardEquality : Equals Equals Question"""
    p[0] = "==?"


def p_WildcardInequality(p):
    """WildcardInequality : Not Equals Question"""
    p[0] = "!=?"


# t_LessThan = r"<"
# t_LessThanEqual = r"<="
def p_LessThanEqual(p):
    """LessThanEqual : LessThan Equals"""
    p[0] = "<="


# t_GreaterThan = r">"
# t_GreaterThanEqual = r">="
def p_GreaterThanEqual(p):
    """GreaterThanEqual : GreaterThan Equals"""
    p[0] = ">="


def p_LogicalAnd(p):
    """LogicalAnd : Amp Amp"""
    p[0] = "&&"


def p_LogicalOr(p):
    """LogicalOr : Bar Bar"""
    p[0] = "||"


def p_BinaryXnor(p):
    """
    BinaryXnor  : Tilde Carat
                | Carat Tilde
    """
    p[0] = "^~"


def p_BinaryNand(p):
    """
    BinaryNand  : Tilde Amp
                | Amp Tilde
    """
    p[0] = "~&"


def p_BinaryNor(p):
    """
    BinaryNor   : Tilde Bar
                | Bar Tilde
    """
    p[0] = "~|"


def p_LogicalImplication(p):
    """LogicalImplication : Minus GreaterThan"""
    p[0] = "->"


def p_LogicalEquivalence(p):
    """LogicalEquivalence : LessThan Minus GreaterThan"""
    p[0] = "<->"


def p_LogicalShiftLeft(p):
    """LogicalShiftLeft : LessThan LessThan"""
    p[0] = "<<"


def p_LogicalShiftRight(p):
    """LogicalShiftRight : GreaterThan GreaterThan"""
    p[0] = ">>"


def p_ArithmeticShiftLeft(p):
    """ArithmeticShiftLeft : LessThan LessThan LessThan"""
    p[0] = "<<<"


def p_ArithmeticShiftRight(p):
    """ArithmeticShiftRight : GreaterThan GreaterThan GreaterThan"""
    p[0] = ">>>"


def p_expression(p):
    "expression : expression1"
    p[0] = p[1]


# ================================================
#   Expressions
# ================================================


def p_expression1_1(p):
    """
    expression1 : expression2
    """
    p[0] = p[1]


def p_expression1_2(p):
    """
    expression1 : expression2 LogicalImplication expression1
                | expression2 LogicalEquivalence expression1
    """
    if p[2] == "->":
        p[0] = ASTOpApply(ASTOp.LogicalImplication, [p[1], p[3]])
    elif p[2] == "<->":
        p[0] = ASTOpApply(ASTOp.LogicalEquivalence, [p[1], p[3]])
    else:
        raise Exception("Unknown operator: " + p[2])


def p_expression2_1(p):
    """
    expression2 : expression3
    """
    p[0] = p[1]


def p_expression2_2(p):
    """
    expression2 : expression3 Question expression Colon expression2
    """
    p[0] = ASTOpApply(ASTOp.ITE, [p[1], p[3], p[5]])


def p_expression3_1(p):
    """
    expression3 : expression4
    """
    p[0] = p[1]


def p_expression3_2(p):
    """
    expression3 : expression3 LogicalOr expression4
                | expression3 LogicalAnd expression4
                | expression3 Bar expression4
                | expression3 Carat expression4
                | expression3 BinaryXnor expression4
                | expression3 Amp expression4
                | expression3 Equality expression4
                | expression3 Inequality expression4
                | expression3 CaseEquality expression4
                | expression3 CaseInequality expression4
                | expression3 WildcardEquality expression4
                | expression3 WildcardInequality expression4
    """
    if p[2] == "||":
        p[0] = ASTOpApply(ASTOp.LogicalOr, [p[1], p[3]])
    elif p[2] == "&&":
        p[0] = ASTOpApply(ASTOp.LogicalAnd, [p[1], p[3]])
    elif p[2] == "|":
        p[0] = ASTOpApply(ASTOp.BinaryOr, [p[1], p[3]])
    elif p[2] == "^":
        p[0] = ASTOpApply(ASTOp.BinaryXor, [p[1], p[3]])
    elif p[2] == "^~":
        p[0] = ASTOpApply(ASTOp.BinaryXnor, [p[1], p[3]])
    elif p[2] == "~^":
        p[0] = ASTOpApply(ASTOp.BinaryXnor, [p[1], p[3]])
    elif p[2] == "&":
        p[0] = ASTOpApply(ASTOp.BinaryAnd, [p[1], p[3]])
    elif p[2] == "==":
        p[0] = ASTOpApply(ASTOp.Equality, [p[1], p[3]])
    elif p[2] == "!=":
        p[0] = ASTOpApply(ASTOp.Inequality, [p[1], p[3]])
    elif p[2] == "===":
        p[0] = ASTOpApply(ASTOp.CaseEquality, [p[1], p[3]])
    elif p[2] == "!==":
        p[0] = ASTOpApply(ASTOp.CaseInequality, [p[1], p[3]])
    elif p[2] == "==?":
        p[0] = ASTOpApply(ASTOp.WildcardEquality, [p[1], p[3]])
    elif p[2] == "!=?":
        p[0] = ASTOpApply(ASTOp.WildcardInequality, [p[1], p[3]])
    else:
        raise Exception("Unknown operator: " + p[2])


def p_expression4_1(p):
    """
    expression4 : expression5
    """
    p[0] = p[1]


def p_expression4_2(p):
    """
    expression4 : expression4 LessThan expression5
                | expression4 LessThanEqual expression5
                | expression4 GreaterThan expression5
                | expression4 GreaterThanEqual expression5
    """
    if p[2] == "<":
        p[0] = ASTOpApply(ASTOp.LessThan, [p[1], p[3]])
    elif p[2] == "<=":
        p[0] = ASTOpApply(ASTOp.LessThanEqual, [p[1], p[3]])
    elif p[2] == ">":
        p[0] = ASTOpApply(ASTOp.GreaterThan, [p[1], p[3]])
    elif p[2] == ">=":
        p[0] = ASTOpApply(ASTOp.GreaterThanEqual, [p[1], p[3]])
    else:
        raise Exception("Unknown operator: " + p[2])


# def p_expression4_3(p):
#     '''
#     expression4 : expression4 KW_inside BraceL open_range_list BraceR
#     '''
#     raise Exception("Not implemented: " + p[2])


def p_expression5_1(p):
    """
    expression5 : expression6
    """
    p[0] = p[1]


def p_expression5_2(p):
    """
    expression5 : expression5 LogicalShiftRight expression6
                | expression5 LogicalShiftLeft expression6
                | expression5 ArithmeticShiftRight expression6
                | expression5 ArithmeticShiftLeft expression6
    """
    if p[2] == ">>":
        p[0] = ASTOpApply(ASTOp.LogicalShiftRight, [p[1], p[3]])
    elif p[2] == "<<":
        p[0] = ASTOpApply(ASTOp.LogicalShiftLeft, [p[1], p[3]])
    elif p[2] == ">>>":
        p[0] = ASTOpApply(ASTOp.ArithmeticShiftRight, [p[1], p[3]])
    elif p[2] == "<<<":
        p[0] = ASTOpApply(ASTOp.ArithmeticShiftLeft, [p[1], p[3]])
    else:
        raise Exception("Unknown operator: " + p[2])


def p_expression6_1(p):
    """
    expression6 : expression7
    """
    p[0] = p[1]


def p_expression6_2(p):
    """
    expression6 : expression6 Plus expression7
                | expression6 Minus expression7
    """
    if p[2] == "+":
        p[0] = ASTOpApply(ASTOp.Add, [p[1], p[3]])
    elif p[2] == "-":
        p[0] = ASTOpApply(ASTOp.Sub, [p[1], p[3]])
    else:
        raise Exception("Unknown operator: " + p[2])


def p_expression7_1(p):
    """
    expression7 : expression8
    """
    p[0] = p[1]


def p_expression7_2(p):
    """
    expression7 : expression7 Star expression8
                | expression7 Divide expression8
                | expression7 Mod expression8
                | expression7 Power expression8
    """
    if p[2] == "*":
        p[0] = ASTOpApply(ASTOp.Mul, [p[1], p[3]])
    elif p[2] == "/":
        p[0] = ASTOpApply(ASTOp.Div, [p[1], p[3]])
    elif p[2] == "%":
        p[0] = ASTOpApply(ASTOp.Mod, [p[1], p[3]])
    elif p[2] == "**":
        p[0] = ASTOpApply(ASTOp.Power, [p[1], p[3]])
    else:
        raise Exception("Unknown operator: " + p[2])


def p_expression8_1(p):
    """
    expression8 : primary
    """
    p[0] = p[1]


def p_expression8_2(p):
    """
    expression8 : Plus primary
                | Minus primary
                | Amp primary
                | BinaryNand primary
                | Bar primary
                | BinaryNor primary
                | Carat primary
                | BinaryXnor primary
                | Not primary
                | Tilde primary
    """
    if p[1] == "+":
        p[0] = ASTOpApply(ASTOp.UnaryPlus, [p[2]])
    elif p[1] == "-":
        p[0] = ASTOpApply(ASTOp.UnaryMinus, [p[2]])
    elif p[1] == "&":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseAnd, [p[2]])
    elif p[1] == "~&" or p[1] == "&~":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseNand, [p[2]])
    elif p[1] == "|":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseOr, [p[2]])
    elif p[1] == "~|" or p[1] == "|~":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseNor, [p[2]])
    elif p[1] == "^":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseXor, [p[2]])
    elif p[1] == "~^" or p[1] == "^~":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseXnor, [p[2]])
    elif p[1] == "!":
        p[0] = ASTOpApply(ASTOp.UnaryLogicalNot, [p[2]])
    elif p[1] == "~":
        p[0] = ASTOpApply(ASTOp.UnaryBitwiseNot, [p[2]])
    else:
        raise Exception("Unknown operator: " + p[1])


# Range expressions
def p_constant_range(p):
    """
    part_select_range   : expression Colon expression
                        | expression PlusColon expression
                        | expression MinusColon expression
    """
    p[0] = ASTRangeIndex(p[1], p[3], p[2])


# ================================================
#   Primitives: number, identifier
# ================================================


def p_number(p):
    """
    number : Num
    """
    if "'" in p[1]:
        # find the base and the size from fragments before and after '
        size, tail = p[1].split("'")
        if "s" == tail[0]:
            p[0] = ASTNumber(tail[2:], tail[1], size)
        else:
            p[0] = ASTNumber(tail[1:], tail[0], size)
    else:
        p[0] = ASTNumber(p[1])

    p[0] = ASTNumber(p[1])


def p_identifier(p):
    """
    identifier : Ident
    """
    p[0] = p[1]


# ================================================
#   Primary signal expressions
# ================================================

# primary1 :: { Expr }
# : identifier                         { EVar $1 }
# | 'this'                             { EThis }
# | primary1 '.' identifier            { EMember $1 (thing $3) }
# | primary1 '[' expression ']'        { ESelect $1 $3 }
# | primary1 '[' part_select_range ']' { ERange $1 $3 }


def p_primary1_1(p):
    """
    primary1 : identifier
    """
    p[0] = ASTIdentifier([(p[1], [])])


def p_primary1_2(p):
    """
    primary1 : KW_this
    """
    p[0] = ASTIdentifier([(THIS_IDENTIFIER, [])])


def p_primary1_3(p):
    """
    primary1 : primary1 Dot identifier
    """
    preident = p[1]
    assert isinstance(
        preident, ASTIdentifier
    ), f"Expected ASTIdentifier, found {preident} in p_primary1_3"
    p[0] = preident.add_level(p[3])


# TODO: need to handle indexing at non-rightmost position
def p_primary1_4(p):
    """
    primary1 : primary1 BracketL expression BracketR
    """
    preident = p[1]
    assert isinstance(
        preident, ASTIdentifier
    ), f"Expected ASTIdentifier, found {preident} in p_primary1_4"
    preindex = p[3]
    assert isinstance(
        preindex, ASTExpr
    ), f"Expected ASTExpr, found {preindex} in p_primary1_4"
    if isinstance(preindex, ASTNumber):
        p[0] = preident.add_level_index(preindex.get_plain_numeric_literal())
    elif isinstance(preindex, ASTIdentifier):
        p[0] = preident.add_level_index(preindex.get_plain_identifier_name())
    else:
        assert (
            False
        ), f"Expected ASTNumber or ASTIdentifier, found {preindex} in p_primary1_4"


def p_primary1_5(p):
    """
    primary1 : primary1 BracketL part_select_range BracketR
    """
    preident = p[1]
    assert isinstance(
        preident, ASTIdentifier
    ), f"Expected ASTIdentifier, found {preident} in p_primary1_5"
    p[0] = preident.select_range(p[3])


# ================================================
#   Function calls
# ================================================

# function_call :: { Expr }
# : identifier '(' sep(',', expression) ')' { EFunctionCall $1 $3 }


def p_function_call(p):
    """
    function_call : identifier ParenL expr_list ParenR
    """
    p[0] = ASTFunctionCall(p[1], p[2])


# ================================================
#   Primary Expressions
# ================================================

# -- A.8.4 Primaries
# primary
# : primary_literal { ELit $1 }
# | primary1 { $1 }
# | empty_unpacked_array_concatenation { error "43" }
# | concatenation {-opt(brackets(range_expression))-} { EConcatenation $1 }
# | multiple_concatenation opt(brackets(range_expression)) { error "45" }
# | function_call { $1 }
# | '(' expression ')' { EParen $2 }
# --X | '(' mintypmax_expression ')' { undefined }
# --X | cast { undefined }
# --X | assignment_pattern_expression { undefined }
# | '$' { undefined }
# | 'null' { undefined }


def p_primary(p):
    """
    primary : number
            | primary1
            | function_call
            | ParenL expression ParenR
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]


# basetype :: { BaseType }
# : 'logic'                                     { TypeLogic }
# | identifier '(' sep(',', expression) ')'     { TypeArgs $1 $3 }
# | identifier                                  { TypeArgs $1 [] }


def p_basetype_1(p):
    """
    basetype : KW_logic
    """
    p[0] = ASTType("logic", [])


def p_basetype_2(p):
    """
    basetype : identifier ParenL expr_list ParenR
    """
    preid = p[1]
    assert isinstance(preid, str), f"Expected str, found {preid} in p_basetype_2"
    p[0] = ASTType(preid, p[3])


def p_basetype_3(p):
    """
    basetype : identifier
    """
    preid = p[1]
    assert isinstance(preid, str), f"Expected str, found {preid} in p_basetype_3"
    p[0] = ASTType(preid, [])


# dimension :: { Dimension }
# : '[' expression ']'                          { Dimension1 $2 }
# | '[' expression ':' expression ']'           { Dimension2 $2 $4 }


def p_dimension_1(p):
    """
    dimension : BracketL expression BracketR
    """
    p[0] = ASTDimension(p[2], None)


def p_dimension_2(p):
    """
    dimension : BracketL expression Colon expression BracketR
    """
    p[0] = ASTDimension(p[2], p[4])


# datatype :: { DataType }
# : basetype list(dimension)                    { DataType $1 $2 }


def p_datatype_1(p):
    """datatype : basetype"""
    p[0] = p[1]


def p_datatype_2(p):
    """datatype : datatype dimension"""
    pretype = p[1]
    assert isinstance(
        pretype, ASTType
    ), f"Expected ASTType, found {pretype} in p_datatype_2"
    p[0] = pretype.add_dimension(p[2])


# caliper_statement :: { Stmt }
# : 'def' sep1(',', expression) ';'             { StmtDef $2 }
# | 'invariant' identifier ':' expression ';'   { StmtInv $2 $4 }
# -- | identifier '(' sep(',', expression) ')' ';' { StmtCall $1 $3 }
# | datatype sep1(',', primary1) ';'            { StmtTypedVar $1 $2 }
# | 'begin' list(caliper_statement) 'end'       { StmtBlock $2 }
# | 'if' '(' expression ')' caliper_statement   { StmtIf $3 $5 }
# | 'foreach' '(' sep1(',', caliper_loop) ')'
#   caliper_statement                           { StmtFor $3 $5 }

# caliper_loop :: { ForLoop }
# : identifier '<' expression { ForLoopLess $1 $3 }
# | identifier 'inside' '[' part_select_range ']' { ForLoopInside $1 $4 }


def p_caliper_loop_1(p):
    """caliper_loop : identifier LessThan expression"""
    preid = p[1]
    assert isinstance(preid, str), f"Expected str, found {preid} in p_caliper_loop_1"
    preexpr = p[3]
    assert isinstance(
        preexpr, ASTNumber
    ), f"Expected ASTNumber, found {preexpr} in p_caliper_loop_1"
    p[0] = (preid, preexpr.get_plain_numeric_literal())


def p_caliper_loop_list_p_1(p):
    """caliper_loop_list_p : caliper_loop"""
    p[0] = [p[1]]


def p_caliper_loop_list_p_2(p):
    """caliper_loop_list_p : caliper_loop_list_p Comma caliper_loop"""
    p[0] = p[1] + [p[3]]


def p_caliper_statement_1(p):
    """
    caliper_statement : KW_def expr_list_p Semi
    """
    p[0] = ASTEq(p[2])


def p_caliper_statement_2(p):
    """
    caliper_statement : KW_invariant identifier Colon expression Semi
    """
    p[0] = ASTInv(p[2], p[4])


def p_caliper_statement_3(p):
    """
    caliper_statement : datatype primary1_list_p Semi
    """
    for prim1 in p[2]:
        assert isinstance(
            prim1, ASTIdentifier
        ), f"Expected ASTIdentifier, found {prim1} in p_caliper_statement_3"
        prim1.datatype = p[1]
    p[0] = ASTEq(p[2])


def p_caliper_statement_4(p):
    """
    caliper_statement : KW_begin caliper_statement_list KW_end
    """
    p[0] = ASTBlock(p[2])


def p_caliper_statement_5(p):
    """
    caliper_statement : KW_if ParenL expression ParenR caliper_statement
    """
    prestmt = p[5]
    assert isinstance(
        prestmt, ASTStmt
    ), f"Expected ASTStmt, found {prestmt} in p_caliper_statement_5"
    prestmt.make_nested()
    p[0] = ASTCondEq(p[3], prestmt)


def p_caliper_statement_6(p):
    """
    caliper_statement : KW_foreach ParenL caliper_loop_list_p ParenR caliper_statement
    """
    prestmt = p[5]
    assert isinstance(
        prestmt, ASTStmt
    ), f"Expected ASTStmt, found {prestmt} in p_caliper_statement_6"
    indexlist = p[3]
    loopstmt = ASTForLoop(indexlist[-1][0], indexlist[-1][1], prestmt)
    # List reverse iteration
    for index in reversed(indexlist[:-1]):
        loopstmt = ASTForLoop(index[0], index[1], loopstmt)
    p[0] = loopstmt


# caliper_mod_stmt :: { ModStmt }
# : 'input' caliper_statement                   { ModStmt Input $2 }
# | 'output' caliper_statement                  { ModStmt Output $2 }
# | 'state' caliper_statement                   { ModStmt Register $2 }
# | 'output' 'state' caliper_statement          { ModStmt OutputReg $3 }
# | 'begin' list(caliper_mod_stmt) 'end'        { ModStmtBlock $2 }
# | 'if' '(' expression ')' caliper_mod_stmt    { ModStmtIf $3 $5 }
# | 'foreach' '(' sep1(',', caliper_loop) ')'
#   caliper_mod_stmt                            { ModStmtFor $3 $5 }
# | 'def' sep1(',', expression) ';'             { ModStmt Internal (StmtDef $2) }
# | 'invariant' identifier ':' expression ';'   { ModStmt Internal (StmtInv $2 $4) }
# -- | identifier '(' sep(',', expression) ')' ';' { ModStmt Internal (StmtCall $1 $3) }
# | datatype sep1(',', primary1) ';'            { ModStmt Internal (StmtTypedVar $1 $2) }
# | 'submodule' identifier '(' sep(',', expression) ')' expression ';'
#                                               { ModStmtInstance $2 $4 $6 }


def p_caliper_mod_stmt_1(p):
    """
    caliper_mod_stmt : KW_input caliper_statement
    """
    p[0] = ASTModInput(p[2])


def p_caliper_mod_stmt_2(p):
    """
    caliper_mod_stmt : KW_output caliper_statement
    """
    p[0] = ASTModOutput(p[2])


def p_caliper_mod_stmt_3(p):
    """
    caliper_mod_stmt : KW_state caliper_statement
    """
    p[0] = ASTModState(p[2])


def p_caliper_mod_stmt_4(p):
    """
    caliper_mod_stmt : KW_output KW_state caliper_statement
    """
    p[0] = ASTModOutputState(p[3])


def p_caliper_mod_stmt_5(p):
    """
    caliper_mod_stmt : KW_begin caliper_mod_stmt_list KW_end
    """
    p[0] = ASTModBlock(p[2])


def p_caliper_mod_stmt_6(p):
    """
    caliper_mod_stmt : KW_if ParenL expression ParenR caliper_mod_stmt
    """
    p[0] = ASTModIf(p[3], p[5])


def p_caliper_mod_stmt_7(p):
    """
    caliper_mod_stmt : KW_def expr_list_p Semi
    """
    logger.error(f"Global `def` not supported, found {p[1]} {p[2]} {p[3]}")
    p[0] = ASTModEq(p[2])


def p_caliper_mod_stmt_8(p):
    """
    caliper_mod_stmt : KW_invariant identifier Colon expression Semi
    """
    p[0] = ASTModInv(p[2], p[4])


def p_caliper_mod_stmt_9(p):
    """
    caliper_mod_stmt : datatype primary1_list_p Semi
    """
    logger.error(f"Global `def` not supported, found {p[1]} {p[2]} {p[3]}")
    for prim1 in p[2]:
        assert isinstance(
            prim1, ASTIdentifier
        ), f"Expected ASTIdentifier, found {prim1} in p_caliper_mod_stmt_9"
        prim1.datatype = p[1]
    p[0] = ASTModEq(p[2])


def p_caliper_mod_stmt_10(p):
    """
    caliper_mod_stmt : KW_submodule identifier ParenL expr_list ParenR identifier Semi
    """
    p[0] = ASTModInstance(p[6], p[2], p[4])


# caliper_declarations :: { [TopDecl] }
# : list(caliper_declaration) { $1 }

# caliper_declaration :: { TopDecl }
# : 'spec' identifier '(' sep(',', identifier) ')' ';'
#   list(caliper_statement)
#   'endspec' { TopDecl $2 $4 $7 }
# | 'struct' identifier '(' sep(',', identifier) ')' ';'
#   list(caliper_statement)
#   'endstruct' { TopDeclStruct $2 $4 $7 }
# | 'module' identifier '(' sep(',', identifier) ')' ';'
#   list(caliper_mod_stmt)
#   'endmodule' { TopDeclModule $2 $4 $7 }
# | 'parameter' identifier ';' { TopDeclParameter $2 Nothing }


def p_caliper_declaration_1(p):
    """
    caliper_declaration : KW_spec identifier ParenL expr_list ParenR Semi caliper_statement_list KW_endspec
    """
    preid = p[2]
    assert isinstance(
        preid, str
    ), f"Expected str, found {preid} in p_caliper_declaration_1"
    p[0] = ASTTopDeclSpec(preid, p[4], p[7])


def p_caliper_declaration_2(p):
    """
    caliper_declaration : KW_struct identifier ParenL expr_list ParenR Semi caliper_statement_list KW_endstruct
    """
    preid = p[2]
    assert isinstance(
        preid, str
    ), f"Expected str, found {preid} in p_caliper_declaration_2"
    p[0] = ASTTopDeclStruct(preid, p[4], p[7])


def p_caliper_declaration_3(p):
    """
    caliper_declaration : KW_module identifier ParenL expr_list ParenR Semi caliper_mod_stmt_list KW_endmodule
    """
    preid = p[2]
    assert isinstance(
        preid, str
    ), f"Expected str, found {preid} in p_caliper_declaration_3"
    p[0] = ASTTopDeclModule(preid, p[4], p[7])


def p_caliper_declaration_4(p):
    """
    caliper_declaration : KW_parameter identifier Semi
    """
    preid = p[2]
    assert isinstance(
        preid, str
    ), f"Expected str, found {preid} in p_caliper_declaration_4"
    p[0] = ASTTopDeclParameter(preid)


def p_caliper_declarations_1(p):
    """
    caliper_declarations : empty
    """
    p[0] = []


def p_caliper_declarations_2(p):
    """
    caliper_declarations : caliper_declaration caliper_declarations
    """
    p[0] = [p[1]] + p[2]


start = "caliper_declarations"


def p_error(p):
    print("Syntax error in input!")


parser = yacc.yacc()

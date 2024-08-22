"""
    PyCaliper

    Author: Adwait Godbole, UC Berkeley

    File: frontend/pycast.py

    AST for representing frontend format
"""

import logging
import sys
from enum import Enum

logger = logging.getLogger(__name__)


class PAST:
    def __init__(self, children=[]):
        self.children = children


class ASTOp(Enum):
    UnaryLogicalNot = 1
    LogicalAnd = 2
    LogicalOr = 3
    BinaryOr = 4
    BinaryAnd = 5
    BinaryXor = 6
    BinaryXnor = 7
    Equality = 9
    Inequality = 10
    CaseEquality = 11
    CaseInequality = 12
    WildcardEquality = 13
    WildcardInequality = 14
    LessThan = 15
    LessThanEqual = 16
    GreaterThan = 17
    GreaterThanEqual = 18
    LogicalShiftRight = 19
    LogicalShiftLeft = 20
    ArithmeticShiftRight = 21
    ArithmeticShiftLeft = 22
    Add = 23
    Sub = 24
    Mul = 25
    Div = 26
    Mod = 27
    Power = 28
    UnaryPlus = 29
    UnaryMinus = 30
    UnaryBitwiseAnd = 31
    UnaryBitwiseOr = 32
    UnaryBitwiseXor = 33
    UnaryBitwiseNot = 34
    UnaryBitwiseNand = 35
    UnaryBitwiseNor = 36
    UnaryBitwiseXnor = 37
    LogicalImplication = 38
    LogicalEquivalence = 39
    ITE = 40


op_to_pyc_lut = {
    ASTOp.UnaryLogicalNot: "UnaryLogicalNot",
    ASTOp.LogicalAnd: "LogicalAnd",
    ASTOp.LogicalOr: "LogicalOr",
    ASTOp.BinaryOr: "BinaryOr",
    ASTOp.BinaryAnd: "BinaryAnd",
    ASTOp.BinaryXor: "BinaryXor",
    ASTOp.BinaryXnor: "BinaryXnor",
    ASTOp.Equality: "Equality",
    ASTOp.Inequality: "Inequality",
    ASTOp.CaseEquality: "CaseEquality",
    ASTOp.CaseInequality: "CaseInequality",
    ASTOp.WildcardEquality: "WildcardEquality",
    ASTOp.WildcardInequality: "WildcardInequality",
    ASTOp.LessThan: "LessThan",
    ASTOp.LessThanEqual: "LessThanEqual",
    ASTOp.GreaterThan: "GreaterThan",
    ASTOp.GreaterThanEqual: "GreaterThanEqual",
    ASTOp.LogicalShiftRight: "LogicalShiftRight",
    ASTOp.LogicalShiftLeft: "LogicalShiftLeft",
    ASTOp.ArithmeticShiftRight: "ArithmeticShiftRight",
    ASTOp.ArithmeticShiftLeft: "ArithmeticShiftLeft",
    ASTOp.Add: "Add",
    ASTOp.Sub: "Sub",
    ASTOp.Mul: "Mul",
    ASTOp.Div: "Div",
    ASTOp.Mod: "Mod",
    ASTOp.Power: "Power",
    ASTOp.UnaryPlus: "UnaryPlus",
    ASTOp.UnaryMinus: "UnaryMinus",
    ASTOp.UnaryBitwiseAnd: "UnaryBitwiseAnd",
    ASTOp.UnaryBitwiseOr: "UnaryBitwiseOr",
    ASTOp.UnaryBitwiseXor: "UnaryBitwiseXor",
    ASTOp.UnaryBitwiseNot: "UnaryBitwiseNot",
    ASTOp.UnaryBitwiseNand: "UnaryBitwiseNand",
    ASTOp.UnaryBitwiseNor: "UnaryBitwiseNor",
    ASTOp.UnaryBitwiseXnor: "UnaryBitwiseXnor",
    ASTOp.LogicalImplication: "LogicalImplication",
    ASTOp.LogicalEquivalence: "LogicalEquivalence",
    ASTOp.ITE: "ITE",
}


class ASTExpr(PAST):
    def __init__(self, children=[]):
        super().__init__(children)
        pass

    def get_plain_identifier_name(self: "ASTExpr"):
        if not isinstance(self, ASTIdentifier):
            logger.error(f"Found non-identifier in plain Identifier check: {self}")
            sys.exit(1)
        elif (self.datatype, self.rng) != (None, None):
            logger.error(
                f"Found non-plain identifier in plain Identifier check: {self}"
            )
            sys.exit(1)
        elif len(self.path) != 1:
            logger.error(f"Found nested identifier in plain Identifier check: {self}")
            sys.exit(1)
        else:
            if self.path[0][1] != []:
                logger.error(
                    f"Found indexed identifier in plain Identifier check: {self}"
                )
                sys.exit(1)
            return self.path[0][0]

    def get_plain_numeric_literal(self: "ASTExpr"):
        if not isinstance(self, ASTNumber):
            logger.error(f"Found non-number in Numeric literal check: {self}")
            sys.exit(1)
        elif (self.base, self.width) != ("", ""):
            logger.error(
                f"Found non-base-free numeric in Numeric literal check: {self}"
            )
            sys.exit(1)
        return self.get_int_value()


class ASTOpApply(ASTExpr):
    def __init__(self, op: ASTOp, args: list[ASTExpr]):
        super().__init__(args)
        self.op = op
        self.args = args


class ASTDimension(PAST):
    """Dimensions of a signal declaration"""

    def __init__(self, start: ASTExpr, end: ASTExpr):
        super().__init__([start, end])
        self.start: ASTExpr = start
        self.end: ASTExpr = end

    def get_plain_width(self):
        if self.start is None and self.end is None:
            return 1
        if self.end is None:
            start = self.start.get_plain_numeric_literal()
            return start + 1
        else:
            start = self.start.get_plain_numeric_literal()
            end = self.end.get_plain_numeric_literal()
            return start - end + 1


class ASTType(PAST):
    def __init__(self, name: str, args: list[ASTExpr], dims: list[ASTDimension] = []):
        super().__init__(args + dims)
        self.name = name
        self.args: list[ASTExpr] = args
        self.dims: list[ASTDimension] = dims

    def add_dimension(self, dim):
        """Adds a dimension to the type. Returns a fresh object."""
        return ASTType(self.name, self.args, self.dims + [dim])

    def is_dimensioned(self):
        return len(self.dims) > 0

    def is_logic(self):
        return self.name == "logic"


class ASTRangeIndex(PAST):
    """Range index"""

    def __init__(self, start: ASTExpr = None, end: ASTExpr = None, step=":"):
        super().__init__([start, end])
        # Range bits
        self.start: ASTExpr = start
        self.end: ASTExpr = end
        self.step = step


THIS_IDENTIFIER = "this"


class ASTIdentifier(ASTExpr):
    def __init__(
        self,
        path: list[str, list[ASTExpr]],
        rng: ASTRangeIndex = None,
        datatype: ASTType = None,
    ):
        super().__init__([rng, datatype])
        self.path: list[tuple[str, list]] = path
        self.rng: ASTRangeIndex = rng
        self.datatype: ASTType = datatype

    def add_level(self, ident: str):
        return ASTIdentifier(self.path + [(ident, [])], self.rng)

    def add_datatype(self, datatype):
        """Adds a datatype to the identifier. In place operation."""
        if self.datatype is not None:
            logger.error(
                f"Identifier {self.path} already has a datatype, cannot re-add. "
                + "Likely the same identifier has been assigned types twice."
            )
            sys.exit(1)
        self.datatype = datatype

    def add_level_index(self, index: int):
        lastlevel = (self.path[-1][0], self.path[-1][1] + [index])
        return ASTIdentifier(self.path[:-1] + [lastlevel], self.rng)

    def select_range(self, rng):
        return ASTIdentifier(self.path, rng)

    def is_this(self) -> bool:
        """Is this identifier the 'this' Caliper keyword?"""
        if len(self.path) == 1 and self.path[0][0] == "this":
            return True
        return False


class ASTNumber(ASTExpr):
    def __init__(self, num: str, base: str = "", width: str = ""):
        super().__init__()
        self.num = num
        self.base = base
        self.width = width

    def get_int_value(self):
        # convert to decimal integer
        if self.base == "":
            return int(self.num)
        return int(self.num, int(self.base))


class ASTFunctionCall(ASTExpr):
    def __init__(self, name: str, args: list[ASTExpr]):
        super().__init__(args)
        self.name = name
        self.args = args


class ASTStmt(PAST):
    def __init__(self, nested=False, children=[]):
        super().__init__(children)
        self.nested = nested

    def make_nested(self):
        self.nested = True


class ASTEq(ASTStmt):
    def __init__(self, exprs: list[ASTExpr]):
        super().__init__(children=exprs)
        self.exprs = exprs


class ASTCondEq(ASTStmt):
    def __init__(self, cond: ASTExpr, stmt: ASTStmt):
        super().__init__(children=[cond, stmt])
        self.cond = cond
        self.stmt = stmt


class ASTInv(ASTStmt):
    def __init__(self, name: str, expr: ASTExpr):
        super().__init__(children=[expr])
        self.name = name
        self.expr = expr


class ASTBlock(ASTStmt):
    def __init__(self, stmts: list[ASTStmt]):
        super().__init__(children=stmts)
        self.stmts = stmts


class ASTForLoop(ASTStmt):
    def __init__(self, loopvar: str, limit: int, stmt: ASTStmt):
        super().__init__(children=[stmt])
        self.loopvar = loopvar
        self.limit = limit
        self.stmt = stmt


# Module statements
class ASTModStmt(PAST):
    def __init__(self, children=[]):
        super().__init__(children)
        pass


class ASTModInput(ASTModStmt):
    def __init__(self, innerstmt):
        super().__init__([innerstmt])
        self.innerstmt = innerstmt


class ASTModOutput(ASTModStmt):
    def __init__(self, innerstmt):
        super().__init__([innerstmt])
        self.innerstmt = innerstmt


class ASTModState(ASTModStmt):
    def __init__(self, innerstmt):
        super().__init__([innerstmt])
        self.innerstmt = innerstmt


class ASTModOutputState(ASTModStmt):
    def __init__(self, innerstmt):
        super().__init__([innerstmt])
        self.innerstmt = innerstmt


class ASTModBlock(ASTModStmt):
    def __init__(self, stmts: list[ASTModStmt]):
        super().__init__(stmts)
        self.stmts = stmts


class ASTModIf(ASTModStmt):
    """if statement macro"""

    def __init__(self, cond: ASTExpr, innerstmt: ASTModStmt):
        super().__init__([cond, innerstmt])
        self.cond = cond
        self.innerstmt = innerstmt


class ASTModEq(ASTModStmt):
    """define in a global context in a module"""

    def __init__(self, exprs: list[ASTExpr]):
        super().__init__(exprs)
        self.exprs = exprs


class ASTModInv(ASTModStmt):
    def __init__(self, name: str, expr: ASTExpr):
        super().__init__([expr])
        self.name = name
        self.expr = expr


class ASTModInstance(ASTModStmt):
    def __init__(self, name: str, subm: str, args: list[ASTExpr]):
        super().__init__(args)
        self.name = name
        self.subm = subm
        self.args = args


# Top declarations
class ASTTopDecl(PAST):
    def __init__(self):
        super().__init__()
        pass


class ASTTopDeclSpec(ASTTopDecl):
    def __init__(self, name: str, args: list[ASTExpr], stmts: list[ASTStmt]):
        super().__init__()
        self.name = name
        self.args = args
        self.stmts = stmts


class ASTTopDeclStruct(ASTTopDecl):
    def __init__(self, name: str, args: list[ASTExpr], stmts: list[ASTStmt]):
        super().__init__()
        self.name = name
        self.args = args
        self.stmts = stmts


class ASTTopDeclModule(ASTTopDecl):
    def __init__(self, name: str, args: list[ASTExpr], stmts: list[ASTModStmt]):
        super().__init__()
        self.name = name
        self.args = args
        self.stmts = stmts


class ASTTopDeclParameter(ASTTopDecl):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

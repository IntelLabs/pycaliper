"""
    PyCaliper

    Author: Adwait Godbole, UC Berkeley

    File: per/per.py

    Internal representation classes for PyCaliper:
        PER (Partial Equivalence Relations):
            A partial equivalence relation defined through equality and
                conditional equality assertions.
        Logic:
            Single bitvectors
        Struct:
            Support for SystemVerilog structs
        Module:
            A module in the specification hierarchy, what else can it be?
"""

import logging
import sys

from enum import Enum
from typing import Callable
import copy
from dataclasses import dataclass

from pycaliper.per.expr import Expr

logger = logging.getLogger(__name__)

UNKNOWN_WIDTH = -1

RESERVED = ["except", "try", "else", "if", "elif"]


def nonreserved_or_fresh(name: str):
    if name in RESERVED:
        return f"{name}_"
    return name


@dataclass
class Path:
    """Path: representing a hierarchical path in the specification.

    path: lis[tuple[str, list]]: at each hierarchical level, string represents identifier and
        the list represents the indexing (if unindexed, then the index is and empty list [])
    slicehigh: int: high index of the slice (default 0)
    slicelow: int: low index of the slice (default 0)
    """

    path: list[tuple[str, list]]
    # Slice of bitvector: low and high indices
    slicelow: int = 0
    slicehigh: int = 0

    def get_hier_path(self, sep=".") -> str:
        """Get the hierarchical path as a string

        Args:
            sep (str, optional): Separator in generated path string. Defaults to '.'.

        Returns:
            str: Path string.
        """
        # No slicing
        if self.slicelow == 0 and self.slicehigh == 0:
            slicestr = ""
        # Single bit
        elif self.slicelow == -1:
            slicestr = f"[{self.slicehigh}]"
        # Proper slice
        else:
            slicestr = f"[{self.slicehigh}:{self.slicelow}]"
        # Base signal string
        if len(self.path) == 0:
            basepath = []
        elif sep == ".":
            basepath = [
                f"{s}{''.join([f'[{i}]' for i in inds])}" for (s, inds) in self.path
            ]
        else:
            basepath = [
                f"{s}{''.join([f'_{i}' for i in inds])}" for (s, inds) in self.path[:-1]
            ]
            basepath += [
                f"{self.path[-1][0]}{''.join([f'[{i}]' for i in self.path[-1][1]])}"
            ]
        return f"{sep.join(basepath)}{slicestr}"

    def get_hier_path_nonindex(self) -> str:
        """Get the hierarchical path string without last level index. Uses '_' as separator.
            For example: a.b[0].c[1] -> a_b_0_c

        Returns:
            str: Path string.
        """
        basepath = [
            f"{s}{''.join([f'_{i}' for i in inds])}" for (s, inds) in self.path[:-1]
        ]
        return f"{'_'.join(basepath + [self.path[-1][0]])}"

    def get_hier_path_flatindex(self) -> str:
        """Get the hierarchical path string with all indices flattened. Uses '_' as separator.
            For example: a.b[0].c[1] -> a_b_0_c_1

        Returns:
            str: Path string.
        """
        basepath = [f"{s}{''.join([f'_{i}' for i in inds])}" for (s, inds) in self.path]
        return f"{'_'.join(basepath)}"

    def add_level_index(self, i: int) -> "Path":
        """Add an index to the last level of the path. For example, a.b[0].c -> a.b[0].c[1]

        Args:
            i (int): index to be added

        Returns:
            Path: new path with the index added.
        """
        lastlevel = (self.path[-1][0], self.path[-1][1] + [i])
        return Path(self.path[:-1] + [lastlevel], self.slicelow, self.slicehigh)

    def add_level(self, name: str) -> "Path":
        """Add a new level to the path. For example, a.b[0] -> a.b[0].c

        Args:
            name (str): name of the new level

        Returns:
            Path: new path with the level added.
        """
        return Path(self.path + [(name, [])], self.slicelow, self.slicehigh)

    def __hash__(self) -> int:
        # Hash (required for dataclasses) based on the path string
        return hash(self.get_hier_path())


class TypedElem:
    """An element in the design hierarchy (Logic, LogicArray, Struct, ...) with a type."""

    def __init__(self):
        self.name = ""
        pass

    def instantiate(self, path: Path):
        logger.error(f"Not implemented instantiate in class: {self.__class__.__name__}")
        sys.exit(1)

    def _typ(self):
        # This is only used for pprinting the type of the element
        logger.error(f"Not implemented _typ in class: {self.__class__.__name__}")
        sys.exit(1)


class Logic(Expr, TypedElem):
    """Class for single bitvectors/signals"""

    def __init__(self, width: int = 1, name: str = "") -> None:
        """
        Args:
            width (int, optional): width of logic signal. Defaults to 1.
            name (str, optional): signal name. Defaults to ''; this is overwritten
                at instantiation time by using the introsepcted attribute name in the parent class.
        """
        # Width of this element, default is 1, UNKNOWN_WIDTH is used for unknown width
        self.width: int = width
        self.name = name
        # Hierarchical path
        self.path: Path = Path([])
        # If member of a logic array, this is the parent array
        self.parent = None

    def instantiate(self, path: Path, parent: "LogicArray" = None) -> "Logic":
        """Instantiate the logic signal with a path and parent array

        Args:
            path (Path): Path object representing the hierarchical path
            parent (LogicArray, optional): Parent array. Defaults to None.

        Returns:
            Logic: return self
        """
        self.path = path
        self.parent = parent
        return self

    def _typ(self):
        if self.width == 1:
            return "logic"
        else:
            return f"logic [{self.width-1}:0]"

    # Call corresponding functions in Path
    def get_hier_path(self, sep: str = "."):
        return self.path.get_hier_path(sep)

    def get_hier_path_nonindex(self):
        return self.path.get_hier_path_nonindex()

    def get_hier_path_flatindex(self):
        return self.path.get_hier_path_flatindex()

    def get_sva(self, pref: str = "a") -> str:
        """
        Args:
            pref (str, optional): Top-level module prefix string. Defaults to 'a'.

        Returns:
            str: SVA representation of the signal.
        """
        return f"{pref}.{self.get_hier_path()}"

    def is_arr_elem(self) -> bool:
        """Check if this signal is an element of an array (inspects the path to see if last level is indexed).

        Returns:
            bool: True if the signal is an array element.
        """
        return len(self.path.path[-1][1]) > 0

    def __str__(self) -> str:
        return self.get_hier_path()

    def __repr__(self):
        return f"self.{self.get_hier_path()}"

    def __call__(self, hi: int, lo: int = -1) -> "Logic":
        """Slice the signal

        Args:
            hi (int): high index of the slice
            lo (int, optional): low index. Defaults to -1 (which means that low index is unsliced).

        Returns:
            Logic: a new signal object representing the slice
        """
        if hi >= self.width or lo < -1 or hi < lo:
            logger.error("Out of bounds: hi=%d, lo=%d, width=%d", hi, lo, self.width)
            sys.exit(1)
        else:
            slicedsig = copy.deepcopy(self)
            slicedsig.path.slicehigh = hi
            slicedsig.path.slicelow = lo
            return slicedsig

    def __hash__(self) -> int:
        # Hash based on the path string.
        return hash(self.get_hier_path())


class LogicArray(TypedElem):
    """An array of logic signals"""

    def __init__(
        self,
        typ_const: Callable[[], TypedElem],
        size: int,
        base: int = 0,
        name: str = "",
    ):
        """An array of logic signals

        Args:
            typ_const (Callable[[], TypedElem]): function that returns a TypedElem object
            size (int): size of the array
            base (int, optional): base index. Defaults to 0.
            name (str, optional): array basename. Defaults to ''.
        """
        self.typ: Callable[[], TypedElem] = typ_const
        self.name: str = name
        self.path: Path = Path([])
        self.size: int = size
        self.base: int = base
        self.logic = [typ_const() for _ in range(size)]

    def instantiate(self, path: Path):
        self.path = path
        for i, o in enumerate(self.logic):
            o.name = f"{self.name}[{i+self.base}]"
            o.instantiate(path.add_level_index(i + self.base), self)
        return self

    def _typ(self):
        return f"{self.typ()._typ()} [{self.base}:{self.base+self.size-1}]"

    def get_hier_path(self, sep: str = "."):
        return self.path.get_hier_path(sep)

    def __getitem__(self, key: int):
        """
        Args:
            key (int): index of the signal, offset by the base index

        Returns:
            TypedElem: signal at the given index
        """
        return self.logic[key - self.base]

    def __str__(self):
        return self.path.get_hier_path()

    def __repr__(self):
        return f"self.{self.name}"

    def __call__(self, index: int) -> TypedElem:
        """
        Args:
            index (int): index of the signal, offset by the base index

        Returns:
            TypedElem: signal at the given index
        """
        return self.logic[index - self.base]


# Partial equivalence relation
class PER:
    """Partial Equivalence Relation (PER) base class"""

    def __init__(self) -> None:
        self.logic: Logic = None

    def __str__(self) -> str:
        raise NotImplementedError("Method not implemented for abstract base PER class.")

    def get_sva(self, cpy1: str, cpy2: str):
        raise NotImplementedError("Method not implemented for abstract base PER class.")


class Eq(PER):
    """Relational equality assertion."""

    def __init__(self, logic: TypedElem) -> None:
        """
        Args:
            logic (TypedElem): the element to be equated
        """
        super().__init__()
        # TODO: add support for non-Logic (struct) types
        if not isinstance(logic, Logic):
            logger.error(f"Invalid PER type: {logic}, currently only Logic supported.")
            sys.exit(1)
        self.logic = logic

    def __str__(self) -> str:
        return f"eq({self.logic})"

    def get_sva(self, cpy1: str = "a", cpy2: str = "b") -> str:
        """
        Args:
            cpy1 (str, optional): Hierarchy prefix of left copy. Defaults to 'a'.
            cpy2 (str, optional): Hierarchy prefix of right copy. Defaults to 'b'.

        Returns:
            str: SVA representation of the equality assertion.
        """
        return f"{self.logic.get_sva(cpy1)} == {self.logic.get_sva(cpy2)}"

    def __repr__(self):
        return f"self.eq({repr(self.logic)})"


class CondEq(PER):
    """Conditional equality assertion"""

    def __init__(self, cond: Expr, logic: Logic) -> None:
        super().__init__()
        self.cond = cond
        self.logic = logic

    def __str__(self) -> str:
        return f"condeq({self.cond}, {self.per})"

    def get_sva(self, cpy1: str = "a", cpy2: str = "b") -> str:
        """Get the SVA representation of the conditional equality assertion."""
        return (
            f"!({self.cond.get_sva(cpy1)} && {self.cond.get_sva(cpy2)}) | "
            + f"({self.logic.get_sva(cpy1)} == {self.logic.get_sva(cpy2)})"
        )

    def __repr__(self):
        return f"self.when({repr(self.cond)})({repr(self.logic)})"


class Inv:
    """Invariant class"""

    def __init__(self, expr: Expr):
        self.expr = expr

    def get_sva(self, pref: str = "a"):
        return self.expr.get_sva(pref)

    def __repr__(self):
        return f"self.inv({repr(self.expr)})"


class Struct(TypedElem):
    """Struct as seen in SV"""

    def __init__(self, name="", **kwargs) -> None:
        self.name = name
        self.params = kwargs
        self.path = Path([])
        self._signals: dict[str, TypedElem] = {}
        self._pycinternal__state: list[PER] = []

    def _typ(self):
        return self.__class__.__name__

    def get_sva(self, pref: str = "a") -> str:
        return f"{pref}.{self.name}"

    def __str__(self) -> str:
        return self.name

    def state(self):
        # Equivalence class definition for this struct
        pass

    def eq(self, expr: Expr) -> None:
        ceq = Eq(expr)
        self._pycinternal__state.append(ceq)

    def when(self, cond: Expr):
        def _lambda(*pers: PER):
            for per in pers:
                if isinstance(per, Logic):
                    ceqs = [CondEq(cond, per)]
                elif isinstance(per, CondEq):
                    ceqs = [CondEq(cond & per.cond, per.logic)]
                elif isinstance(per, LogicArray):
                    ceqs = [CondEq(cond, p) for p in per.logic]
                else:
                    logger.error(f"Invalid PER type: {per}")
                    sys.exit(1)
            self._pycinternal__state.extend(ceqs)

        return _lambda

    def instantiate(self, path: Path):
        self.path = path
        sigattrs = {}
        for attr in dir(self):
            obj = getattr(self, attr)
            if (
                isinstance(obj, Logic)
                or isinstance(obj, LogicArray)
                or isinstance(obj, Struct)
            ):
                # Assign name if not provided during declaration
                if obj.name == "":
                    obj.name = attr
                sigattrs[obj.name] = obj.instantiate(path.add_level(obj.name))
        self._signals = sigattrs
        # INFO: This is not yet supported.
        # TODO: support state equality definitions for structs
        # self.state()
        return self

    def _typ(self) -> str:
        return f"{self.__class__.__name__}"

    def sprint(self) -> str:
        """Pretty string for the struct definition"""
        s = ""
        s += f"struct {self.name}({self.__class__.__name__})"
        s += "signals:\n"
        for k, v in self._signals.items():
            s += f"\t{k} : {v._typ()}\n"
        s += "state:\n"
        for i in self._pycinternal__state:
            s += f"\t{i}\n"
        return s

    def pprint(self):
        """Pretty print the struct definition"""
        print(self.sprint())

    def get_repr(self, reprs):
        reprs[self.__class__.__name__] = repr(self)
        for s, t in self._signals.items():
            if isinstance(t, Struct):
                if t.__class__.__name__ not in reprs:
                    reprs = t.get_repr(reprs)
        return reprs

    def __repr__(self):
        """Generate Python code for the struct definition"""
        inits = ["\tdef __init__(self, name = ''):", f"\t\tsuper().__init__(name)"]
        for s, t in self._signals.items():
            if isinstance(t, Logic):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = Logic({t.width}, "{t.name}")'
                )
            elif isinstance(t, LogicArray):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = LogicArray(lambda: Logic({t.typ().width}), {t.size}, "{t.name}")'
                )
            elif isinstance(t, Struct):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = {t.__class__.__name__}("{t.name}")'
                )
            else:
                logger.error(f"Invalid signal type: {t}")
                sys.exit(1)
        initstring = "\n".join(inits)

        return f"""
class {self.__class__.__name__}(Struct):

{initstring}
        """


class Group:
    """A hierarchical group; does not have any hierarchical position associated with itself."""

    def __init__(self, name: str = ""):
        self.name = name
        self._elems: dict[str, TypedElem] = {}

    def instantiate(self, path: Path):
        for attr in dir(self):
            obj = getattr(self, attr)
            if (
                isinstance(obj, Logic)
                or isinstance(obj, LogicArray)
                or isinstance(obj, Struct)
                or isinstance(obj, Module)
            ):
                if obj.name == "":
                    obj.name = attr
                self._elems[obj.name] = obj.instantiate(path.add_level(obj.name))
        return self

    def get_repr(self, reprs):
        reprs[self.__class__.__name__] = repr(self)
        for s, t in self._elems.items():
            if isinstance(t, Struct) or isinstance(t, Module):
                if t.__class__.__name__ not in reprs:
                    reprs = t.get_repr(reprs)
        return reprs

    def __repr__(self):

        inits = ["\tdef __init__(self, name = ''):", f"\t\tsuper().__init__(name)"]
        for s, t in self._elems.items():
            if isinstance(t, Logic):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = Logic({t.width}, "{t.name}")'
                )
            elif isinstance(t, LogicArray):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = LogicArray(lambda: Logic({t.typ().width}), {t.size}, "{t.name}")'
                )
            elif isinstance(t, Struct):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = {t.__class__.__name__}("{t.name}")'
                )
            elif isinstance(t, Module):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = {t.__class__.__name__}("{t.name}", {t.params})'
                )
            else:
                logger.error(f"Invalid signal type: {t}")
                sys.exit(1)
        initstring = "\n".join(inits)

        return f"""
class {self.__class__.__name__}(Group):

{initstring}
        """


class SVFuncApply(Expr):
    """Apply a SystemVerilog function to a list of arguments"""

    def __init__(self, func: "SVFunc", args: tuple[Expr]) -> None:
        self.func = func
        self.args = args

    def get_sva(self, pref: str = "a") -> str:
        """Get the SVA representation of the function application."""
        return f"{self.func}({', '.join([a.get_sva(pref) for a in self.args])})"


class SVFunc:
    def __init__(self, name=""):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __call__(self, *args):
        return SVFuncApply(self, args)


class Context(Enum):
    """Context of specification declarations made within a module."""

    INPUT = 0
    STATE = 1
    OUTPUT = 2


class Hole:
    """A synthesis hole"""

    def __init__(self):
        self.active = True
        pass

    def deactivate(self):
        self.active = False


class PERHole(Hole):
    """A synthesis hole for a PER"""

    def __init__(self, per: PER, ctx: Context):
        super().__init__()
        self.per = per
        self.ctx = ctx

    def __repr__(self):
        return f"self.eqhole([{repr(self.per.logic)}])"


class CtrAlignHole(Hole):
    def __init__(self, ctr: Logic, sigs: list[Logic]):
        super().__init__()
        self.ctr = ctr
        self.sigs = sigs

    def __repr__(self) -> str:
        return f"self.ctralignhole({repr(self.ctr)}, {repr(self.sigs)})"


def when(cond: Expr):
    """Create a Conditional equality PER generator. This returns a lambda that returns a CondEq object.

    Args:
        cond (Expr): the condition to apply the PER under
    """

    def _lambda(per: PER):
        if isinstance(per, Eq):
            return CondEq(cond, per.logic)
        elif isinstance(per, CondEq):
            return CondEq(cond & per.cond, per.logic)
        else:
            logger.error(f"Invalid PER type: {per}")
            sys.exit(1)

    return _lambda


class Module:
    """Module class for specifications related to a SV HW module"""

    def __init__(self, name="", **kwargs) -> None:
        """
        Args:
            name (str, optional): non-default module name in the hierarchy. Defaults to '' which is
                overriden by the attribute name.
        """
        self.name = name
        self.path: Path = Path([])
        self.params = kwargs
        # Internal (private) members
        # Has this module been elaborated (based on a top module)
        self._instantiated = False
        # _context keeps track of the scope in which declarations/specifications are being generated
        self._context = Context.INPUT
        # Logic, LogicArray, Struct
        self._signals: dict[str, TypedElem] = {}
        self._groups: dict[str, Group] = {}
        self._functions: dict[str, SVFunc] = {}
        self._submodules: dict[str, Module] = {}
        # PER specifications for input, state and output scopes
        self._pycinternal__input: list[PER] = []
        self._pycinternal__state: list[PER] = []
        self._pycinternal__output: list[PER] = []
        # Single trace specifications for input, state and output scopes
        self._pycinternal__input_invs: list[Inv] = []
        self._pycinternal__state_invs: list[Inv] = []
        self._pycinternal__output_invs: list[Inv] = []
        # PER holes
        self._perholes: list[PERHole] = []
        # CtrAlign holes
        self._caholes: list[CtrAlignHole] = []

    # Invariant functions to be overloaded by descendant specification classes
    def input(self) -> None:
        pass

    def state(self) -> None:
        pass

    def output(self) -> None:
        pass

    def eq(self, *elems: TypedElem) -> None:
        """Create an relational equality invariant"""
        eqs = []
        for elem in elems:
            if isinstance(elem, Logic):
                eqs.append(Eq(elem))
            elif isinstance(elem, LogicArray):
                eqs.extend([Eq(l) for l in elem.logic])
            elif isinstance(elem, Struct):
                logger.error("Structs are not yet supported in Eq invariants.")
        if self._context == Context.INPUT:
            self._pycinternal__input.extend(eqs)
        elif self._context == Context.STATE:
            self._pycinternal__state.extend(eqs)
        elif self._context == Context.OUTPUT:
            self._pycinternal__output.extend(eqs)
        else:
            raise Exception("Invalid context")

    def _eq(self, elem: Logic, ctx: Context) -> None:
        """Add equality property with the specified context.

        Args:
            elem (Logic): the invariant expression.
            ctx (Context): the context to add this invariant under.
        """
        if ctx == Context.INPUT:
            self._pycinternal__input_invs.append(Eq(elem))
        elif ctx == Context.STATE:
            self._pycinternal__state_invs.append(Eq(elem))
        else:
            self._pycinternal__output_invs.append(Eq(elem))

    def when(self, cond: Expr) -> Callable:
        """Conditional equality PER.

        Args:
            cond (Expr): the condition Expr to enforce nested PER under.

        Returns:
            Callable: a lambda that is applied to the nested PER.
        """

        def _lambda(*pers: PER):
            for per in pers:
                if isinstance(per, Logic):
                    ceqs = [CondEq(cond, per)]
                elif isinstance(per, CondEq):
                    ceqs = [CondEq(cond & per.cond, per.logic)]
                elif isinstance(per, LogicArray):
                    ceqs = [CondEq(cond, p) for p in per.logic]
                else:
                    logger.error(f"Invalid PER type: {per}")
                    sys.exit(1)
                if self._context == Context.INPUT:
                    self._pycinternal__input.extend(ceqs)
                elif self._context == Context.STATE:
                    self._pycinternal__state.extend(ceqs)
                elif self._context == Context.OUTPUT:
                    self._pycinternal__output.extend(ceqs)

        return _lambda

    def eqhole(self, exprs: list[Expr]):
        """Creates an Eq (synthesis) hole.

        Args:
            exprs (list[Expr]): the list of expressions to consider as candidates for filling this hole.
        """
        if self._context == Context.INPUT or self._context == Context.OUTPUT:
            logger.error("Holes in input/output contexts currently not supported")
            sys.exit(1)
        for expr in exprs:
            self._perholes.append(PERHole(Eq(expr), self._context))

    def ctralignhole(self, ctr: Logic, sigs: list[Logic]):
        """Creates a Control Alignment hole.

        Args:
            ctr (Logic): the control signal that the branch conditions are based on.
            sigs (list[Logic]): the signals to learn lookup tables for.
        """
        if self._context == Context.INPUT or self._context == Context.OUTPUT:
            logger.error("Holes in input/output contexts currently not supported")
            sys.exit(1)
        self._caholes.append(CtrAlignHole(ctr, sigs))

    def inv(self, expr: Expr) -> None:
        """Add single trace invariants to the current context.

        Args:
            expr (Expr): the invariant expression.
        """
        if self._context == Context.INPUT:
            self._pycinternal__input_invs.append(Inv(expr))
        elif self._context == Context.STATE:
            self._pycinternal__state_invs.append(Inv(expr))
        else:
            self._pycinternal__output_invs.append(Inv(expr))

    def _inv(self, expr: Expr, ctx: Context) -> None:
        """Add single trace invariants with the specified context.

        Args:
            expr (Expr): the invariant expression.
            ctx (Context): the context to add this invariant under.
        """
        if ctx == Context.INPUT:
            self._pycinternal__input_invs.append(Inv(expr))
        elif ctx == Context.STATE:
            self._pycinternal__state_invs.append(Inv(expr))
        else:
            self._pycinternal__output_invs.append(Inv(expr))

    def instantiate(self, path: Path = Path([])) -> "Module":
        """Instantiate the current Module.

        Args:
            path (Path, optional): The path in the hierarchy to place this module at. Defaults to Path([]).

        Returns:
            Module: return the instantiated module.
        """
        if self._instantiated:
            logger.warning("Module already instantiated, skipping.")
            return
        self.path = path
        # Add all signals (Logic, LogicArray, Structs), groups, functions and submodules.
        sigattrs = {}
        groupattrs = {}
        funcattrs = {}
        submoduleattrs = {}
        for attr in dir(self):
            obj = getattr(self, attr)
            if (
                isinstance(obj, Logic)
                or isinstance(obj, LogicArray)
                or isinstance(obj, Struct)
            ):
                # Allow different dict key and signal names
                if obj.name == "":
                    obj.name = attr
                sigattrs[obj.name] = obj.instantiate(path.add_level(obj.name))
            elif isinstance(obj, Group):
                if obj.name == "":
                    obj.name = attr
                groupattrs[obj.name] = obj.instantiate(path.add_level(obj.name))
            elif isinstance(obj, SVFunc):
                if obj.name == "":
                    obj.name = attr
                funcattrs[obj.name] = obj
            elif isinstance(obj, Module):
                if obj.name == "":
                    obj.name = attr
                submoduleattrs[obj.name] = obj.instantiate(path.add_level(obj.name))
        self._signals = sigattrs
        self._groups = groupattrs
        self._functions = funcattrs
        self._submodules = submoduleattrs
        # Call the specification generator methods.
        self._context = Context.INPUT
        self.input()
        self._context = Context.STATE
        self.state()
        self._context = Context.OUTPUT
        self.output()
        self._instantiated = True
        return self

    def get_hier_path(self, sep: str = "."):
        """Call inner get_hier_path method."""
        return self.path.get_hier_path(sep)

    def sprint(self):
        s = ""
        s += f"module {self.__class__.__name__}\n"
        s += "signals:\n"
        for k, v in self._signals.items():
            s += f"\t{k} : {v._typ()}\n"
        s += "submodules:\n"
        for k, v in self._submodules.items():
            s += f"\t{k} : {v.__class__.__name__}\n"
        s += "input:\n"
        for i in self._pycinternal__input:
            s += f"\t{i}\n"
        s += "state:\n"
        for i in self._pycinternal__state:
            s += f"\t{i}\n"
        s += "output:\n"
        for i in self._pycinternal__output:
            s += f"\t{i}\n"
        if self._perholes:
            s += "perholes:\n"
            for i in self._perholes:
                s += f"\t{i.per} ({i.ctx})\n"
        return s

    def get_repr(self, reprs):
        # Find all submodules and structs that need to be defined
        reprs[self.__class__.__name__] = repr(self)
        for s, t in self._signals.items():
            if isinstance(t, Struct):
                if t.__class__.__name__ not in reprs:
                    reprs = t.get_repr(reprs)
        for s, t in self._groups.items():
            if t.__class__.__name__ not in reprs:
                reprs = t.get_repr(reprs)

        for s, t in self._submodules.items():
            if t.__class__.__name__ not in reprs:
                reprs = t.get_repr(reprs)
        return reprs

    def full_repr(self):
        reprs = self.get_repr({})
        s = "from pycaliper.per import *\n\n"
        for k, v in reprs.items():
            s += f"{v}\n"
        return s

    def __repr__(self):
        """Create the repr string."""
        inits = [
            "\tdef __init__(self, name = '', **kwargs):",
            f"\t\tsuper().__init__(name, kwargs)",
        ]
        for s, t in self._signals.items():
            if isinstance(t, Logic):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = Logic({t.width}, "{t.name}")'
                )
            elif isinstance(t, LogicArray):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = LogicArray(lambda: Logic({t.typ().width}), {t.size}, "{t.name}")'
                )
            elif isinstance(t, Struct):
                inits.append(
                    f'\t\tself.{nonreserved_or_fresh(t.name)} = {t.__class__.__name__}("{t.name}")'
                )
            else:
                logger.error(f"Invalid signal type: {t}")
                sys.exit(1)
        for s, t in self._groups.items():
            inits.append(
                f'\t\tself.{nonreserved_or_fresh(t.name)} = {t.__class__.__name__}("{t.name}")'
            )
        initstring = "\n".join(inits)
        for s, t in self._submodules.items():
            inits.append(
                f'\t\tself.{nonreserved_or_fresh(t.name)} = {t.__class__.__name__}("{t.name}", {t.params})'
            )
        initstring = "\n".join(inits)

        inputs = (
            ["\tdef input(self):"]
            + [f"\t\t{repr(t)}" for t in self._pycinternal__input]
            + [f"\t\t{repr(t)}" for t in self._pycinternal__input_invs]
            + ["\t\tpass"]
        )
        inputstring = "\n".join(inputs)

        outputs = (
            ["\tdef output(self):"]
            + [f"\t\t{repr(t)}" for t in self._pycinternal__output]
            + [f"\t\t{repr(t)}" for t in self._pycinternal__output_invs]
            + ["\t\tpass"]
        )
        outputstring = "\n".join(outputs)

        states = (
            ["\tdef state(self):"]
            + [f"\t\t{repr(t)}" for t in self._pycinternal__state]
            + [f"\t\t{repr(t)}" for t in self._pycinternal__state_invs]
            + [f"\t\t{repr(t)}" for t in self._perholes if t.active]
            + ["\t\tpass"]
        )
        statestring = "\n".join(states)

        return f"""

class {self.__class__.__name__}(Module):

{initstring}

{inputstring}

{outputstring}

{statestring}
        """

    def pprint(self):
        print(self.sprint())


# SVA-specific functions
past = SVFunc("$past")
stable = SVFunc("$stable")
fell = SVFunc("$fell")
rose = SVFunc("$rose")

from io import StringIO
import logging
import sys

from typing import Optional

from pycaliper.frontend.pycast import *

from pycaliper.frontend.genericpass import GenericPass

logger = logging.getLogger(__name__)


class TopDeclPass(GenericPass):
    def __init__(self):
        super().__init__(
            "TopDeclPass", "Identifies modules and structs in the specification."
        )
        self.modules = {}
        self.structs = {}

    def visit_ASTTopDeclModule(self, node):
        assert isinstance(node, ASTTopDeclModule)
        self.modules[node.name] = node

    def visit_ASTTopDeclStruct(self, node):
        assert isinstance(node, ASTTopDeclStruct)
        self.structs[node.name] = node

    def run(self, ast):
        self.visit(ast)
        return (self.modules, self.structs)


def create_pyc_variable(name: str, index: int):
    return f"_pyc_{name}_{index}_"


class PYCGenPass(GenericPass):
    def __init__(self):
        super().__init__("PYCGenPass", "Converts AST to PYC DSL code.")
        self.submodules = {}
        # Declarations of only certain signals from an array, the declared indices are
        # stored here here keyed by the array name
        self.incompletearrays: dict[str, set] = {}
        self.variables: dict[str, ASTType] = {}
        self.submodstructs = set()

        # name and parameters
        self.objname = ""
        self.parameters = []

        # Functions
        self.init = []
        self.input = []
        self.state = []
        self.output = []

        self.loop_scopes = []
        self.loop_iterators = {}

        self.outstream = None

    def reset(self):
        self.submodules: dict[str, ASTModInstance] = {}

        self.incompletearrays: dict[str, set] = {}
        self.variables: dict[str, ASTType] = {}
        self.submodstructs = set()

        # name and parameters
        self.objname = ""
        self.parameters = []

        # Functions
        self.init = []
        self.input = []
        self.state = []
        self.output = []

        self.loop_scopes = []
        self.loop_iterators: dict[str, int] = {}

    def push_loop_scope(self, loopvar: str):
        if loopvar in self.loop_scopes:
            logger.error(f"Loop iterator {loopvar} is declared in parent scope")
            sys.exit(1)
        self.loop_scopes.append(loopvar)
        self.loop_iterators[loopvar] = -1

    def increment_loop_iterator(self):
        self.loop_iterators[self.loop_scopes[-1]] += 1

    def pop_loop_scope(self):
        del self.loop_iterators[self.loop_scopes[-1]]
        self.loop_scopes = self.loop_scopes[:-1]

    def evaluate_index(self, index):
        if isinstance(index, int):
            return index
        else:
            return self.loop_iterators.get(index, -1)

    def type_to_pyc_repr(self, dt: Optional[ASTType]):

        if dt is None:
            logger.warning("Type is None, defaulting to Logic().")
            return "Logic()"
        elif dt.is_logic():
            if not dt.is_dimensioned():
                return "Logic()"
            else:
                sizedim = dt.dims[-1]
                typestr = f"Logic({sizedim.get_plain_width()})"
                if len(dt.dims) == 1:
                    return typestr
                elif len(dt.dims) == 2:
                    arraydim = dt.dims[-2]
                    return (
                        f"LogicArray(lambda: {typestr}, {arraydim.get_plain_width()})"
                    )
                else:
                    logger.error(
                        f"Only 1D arrays are supported, found {len(dt.dims)-1}-D array."
                    )
                    sys.exit(1)
        else:
            arglist = ", ".join([self.visit(arg) for arg in dt.args])
            typestr = f"{dt.name}({arglist})"
            if not dt.is_dimensioned():
                return typestr
            elif len(dt.dims) == 1:
                arraydim = dt.dims[-2]
                return f"LogicArray(lambda: {typestr}, {arraydim.get_plain_width()})"
            else:
                logger.error(
                    f"Struct arrays are unsupported, found {len(dt.dims)-1}-D struct array."
                )
                sys.exit(1)

    def visit_ASTModInstance(self, node):
        assert isinstance(node, ASTModInstance)
        self.submodules[node.name] = node
        argstring = ", ".join([self.visit(arg) for arg in node.args])
        self.init.append(f"self.{node.name} = {node.subm}({argstring})")

    def visit_ASTNumber(self, node: ASTNumber):
        # Check if this has a specified base and width
        if node.base != "" and node.width != "":
            return f"Const({node.get_int_value()}, {node.width})"
        elif node.base != "":
            return f"Const({node.get_int_value()})"
        return node.num

    def visit_ASTOpApply(self, node: ASTOpApply):
        argstring = ", ".join([self.visit(expr) for expr in node.args])
        return f"OpApply({op_to_pyc_lut[node.op]}(), [{argstring}])"

    def visit_ASTRangeIndex(self, node: ASTRangeIndex):
        if node.step != ":":
            logger.error(f"Non-default step not supported, found in node: {node}")
            sys.exit(1)
        if node.start is None:
            return ""
        elif node.end is None:
            return f"({self.visit(node.start)})"
        else:
            return f"({self.visit(node.start)}, {self.visit(node.end)})"

    def visit_ASTIdentifier(self, node):

        assert isinstance(node, ASTIdentifier)
        if len(node.path) == 0:
            logger.error(f"Path must have atleast one element, found 0: {node}")
            sys.exit(1)
        elif node.is_this():
            # This node is the 'this' keyword
            return "self"
        elif len(node.path) == 1:
            # This is not a node from a subhierarchy, this needs to be instantiated directly
            name = node.path[0][0]
            indexlist = node.path[0][1]
            # Need to create a declaration
            if name not in self.variables:
                # First declaration for the basename
                self.variables[name] = node.datatype
                if indexlist != []:
                    if len(indexlist) > 1:
                        logger.error(
                            "One-off index declarations not supported for non 1D arrays"
                        )
                        sys.exit(1)
                    index = self.evaluate_index(indexlist[0])
                    nameindex = create_pyc_variable(name, index)
                    # This is a index-subset declaration
                    self.init.append(
                        f"self.{nameindex} = {self.type_to_pyc_repr(node.datatype)}"
                    )
                    self.incompletearrays[name] = set([index])
                else:
                    # This is a full declaration
                    self.init.append(
                        f"self.{name} = {self.type_to_pyc_repr(node.datatype)}"
                    )
            elif name in self.incompletearrays:
                # Another cherry-picked index
                if len(indexlist) != 1:
                    logger.error(
                        "Cherry picked index has index-list length other than 1"
                    )
                    sys.exit(1)
                index = self.evaluate_index(indexlist[0])
                if index not in self.incompletearrays[name]:
                    # First time seeing this
                    nameindex = create_pyc_variable(name, index)
                    # This is a index-subset declaration
                    self.init.append(
                        f"self.{nameindex} = {self.type_to_pyc_repr(node.datatype)}"
                    )
                    self.incompletearrays[name].add(index)
        else:
            # This is a node from a hierarchical element
            name = node.path[0][0]
            self.submodstructs.add(name)

        indexedpath = []
        for (s, inds) in node.path:
            indices = [f"[{self.evaluate_index(i)}]" for i in inds]
            indexedpath.append(f"{s}{''.join(indices)}")
        indexedstr = f"self.{'.'.join(indexedpath)}"
        if node.rng is None:
            rangestr = ""
        else:
            rangestr = self.visit(node.rng)
        return f"{indexedstr}{rangestr}"

    def visit_ASTFunctionCall(self, node: ASTFunctionCall):
        argstring = ",".join([self.visit(expr) for expr in node.args])
        return f"self.{node.name}({argstring})"

    # Statements
    def visit_ASTEq(self, node: ASTEq):
        if node.nested:
            return [self.visit(expr) for expr in node.exprs]
        return [f"self.eq({self.visit(expr)})" for expr in node.exprs]

    def visit_ASTCondEq(self, node: ASTCondEq):
        condstring = self.visit(node.cond)
        # Propagate nesting
        node.stmt.make_nested()
        stmtstrings = self.visit(node.stmt)
        if node.nested:
            return [f"when({condstring})({s})" for s in stmtstrings]
        return [f"self.when({condstring})({s})" for s in stmtstrings]

    def visit_ASTInv(self, node: ASTInv):
        if node.nested:
            logger.error(f"Nested invariants are not supported, found: {node}")
            sys.exit(1)
        invstring = self.visit(node.expr)
        return [f"self.inv({invstring})"]

    def visit_ASTBlock(self, node: ASTBlock):
        if node.nested:
            for s in node.stmts:
                s.make_nested()
        return [s for stmt in node.stmts for s in self.visit(stmt)]

    def visit_ASTForLoop(self, node: ASTForLoop):
        if node.nested:
            node.stmt.make_nested()
        stmts = []
        self.push_loop_scope(node.loopvar)
        for i in range(node.limit):
            self.increment_loop_iterator()
            stmts += self.visit(node.stmt)
        self.pop_loop_scope()
        return stmts

    def visit_ASTModInput(self, node: ASTModInput):
        self.input.extend(self.visit(node.innerstmt))

    def visit_ASTModOutput(self, node: ASTModOutput):
        self.output.extend(self.visit(node.innerstmt))

    def visit_ASTModState(self, node: ASTModState):
        self.state.extend(self.visit(node.innerstmt))

    def visit_ASTModOutputState(self, node: ASTModOutputState):
        logger.error("ASTModOutputState is not supported")
        sys.exit(1)

    def visit_ASTModBlock(self, node: ASTModBlock):
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_ASTModIf(self, node: ASTModIf):
        logger.error(f"ASTModIf is not currently supported: {node}")
        sys.exit(1)

    def visit_ASTModEq(self, node: ASTModEq):
        logger.error(f"ASTModEq is not currently supported: {node}")
        sys.exit(1)

    def visit_ASTModInv(self, node: ASTModInv):
        logger.error(f"ASTModInv is not currently supported: {node}")
        sys.exit(1)

    def generate_struct_repr(self):
        paramstring = "".join([f", {p}" for p in self.parameters])
        inits = (
            [
                f"\tdef __init__(self {paramstring}, name = ''):",
                f"\t\tsuper().__init__(name)",
            ]
            + [f"\t\tself.{p} = {p}" for p in self.parameters]
            + [f"\t\t{s}" for s in self.init]
        )
        initstring = "\n".join(inits)

        states = (
            ["\tdef state(self):"] + [f"\t\t{s}" for s in self.state] + ["\t\tpass"]
        )
        statestring = "\n".join(states)

        return f"""
class {self.objname}(Struct):

{initstring}

{statestring}
        """

    def generate_module_repr(self):
        paramstring = "".join([f", {p}" for p in self.parameters])
        inits = (
            [
                f"\tdef __init__(self {paramstring}, name = ''):",
                f"\t\tsuper().__init__(name)",
            ]
            + [f"\t\tself.{p} = {p}" for p in self.parameters]
            + [f"\t\t{s}" for s in self.init]
        )
        for name, indices in self.incompletearrays.items():
            inits.append(f"\t\tself.{name} = dict()")
            for ind in indices:
                inits.append(
                    f"\t\tself.{name}[{ind}] = {create_pyc_variable(name, ind)}"
                )
        initstring = "\n".join(inits)

        inputs = (
            ["\tdef input(self):"] + [f"\t\t{s}" for s in self.input] + ["\t\tpass"]
        )
        inputstring = "\n".join(inputs)

        outputs = (
            ["\tdef output(self):"] + [f"\t\t{s}" for s in self.output] + ["\t\tpass"]
        )
        outputstring = "\n".join(outputs)

        states = (
            ["\tdef state(self):"] + [f"\t\t{s}" for s in self.state] + ["\t\tpass"]
        )
        statestring = "\n".join(states)

        return f"""
class {self.objname}(Module):

{initstring}

{inputstring}

{outputstring}

{statestring}
        """

    def run(self, decls: list[ASTTopDecl]):

        # Create a stringIO
        self.outstream = StringIO()

        for decl in decls:
            self.reset()
            if isinstance(decl, ASTTopDeclModule):
                # Collect module name and parameters
                objname = decl.name
                self.objname = objname
                for arg in decl.args:
                    argname = arg.get_plain_identifier_name()
                    self.parameters.append(argname)
                self.visit(decl.stmts)
                self.outstream.write(self.generate_module_repr())
            elif isinstance(decl, ASTTopDeclStruct):
                objname = decl.name
                self.objname = objname

                for arg in decl.args:
                    argname = arg.get_plain_identifier_name()
                    self.parameters.append(argname)
                for stmt in decl.stmts:
                    self.state.extend(self.visit(stmt))
                self.outstream.write(self.generate_struct_repr())
            else:
                logger.warn(
                    f"Expected ASTTopDeclModule, got {decl.__class__.__name__}. Ignoring!"
                )

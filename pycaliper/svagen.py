"""
    Generate SVA (wires, assumes, asserts) for specifications in PER
"""

import sys
import logging
from pydantic import BaseModel

from .per import Module, Eq, Path, Context, PER, Inv, PERHole, AuxModule
from .propns import *

logger = logging.getLogger(__name__)


# Internal signals
COUNTER = "_pycinternal__counter"
STEP_SIGNAL = "_pycinternal__step"


def step_signal(k: int):
    return f"{STEP_SIGNAL}_{k}"


# def step_property(k: int):
#     return f"step_{k}"

# Internal wire names
def eq_sva(s: str):
    return f"eq_{s}"


def condeq_sva(s: str):
    return f"condeq_{s}"


def per_sva(mod: Module, ctx: Context):
    if ctx == Context.INPUT:
        return f"{mod.get_hier_path('_')}_input"
    elif ctx == Context.STATE:
        return f"{mod.get_hier_path('_')}_state"
    elif ctx == Context.OUTPUT:
        return f"{mod.get_hier_path('_')}_output"
    else:
        logger.error(f"Invalid context {ctx}")
        sys.exit(1)


def inv_sva(mod: Module, ctx: Context):
    if ctx == Context.INPUT:
        return f"{mod.get_hier_path('_')}_input_inv"
    elif ctx == Context.STATE:
        return f"{mod.get_hier_path('_')}_state_inv"
    elif ctx == Context.OUTPUT:
        return f"{mod.get_hier_path('_')}_output_inv"
    else:
        logger.error(f"Invalid context {ctx}")
        sys.exit(1)


class ModuleSpec(BaseModel):
    # Module path
    path: Path
    input_spec_decl: str
    state_spec_decl: str
    output_spec_decl: str
    input_inv_spec_decl_comp: str
    state_inv_spec_decl_comp: str
    output_inv_spec_decl_comp: str
    input_inv_spec_decl_single: str
    state_inv_spec_decl_single: str
    output_inv_spec_decl_single: str


class SVAContext(BaseModel):
    holes: list[str] = []
    assms_2trace: list[str] = []
    asrts_2trace: list[str] = []
    assms_1trace: list[str] = []
    asrts_1trace: list[str] = []
    assms_bmc: list[str] = []
    asrts_bmc: list[str] = []


class SVAGen:
    def __init__(self, topmod: Module) -> None:
        self.topmod = topmod
        self.specs: dict[Path, ModuleSpec] = {}

        self.holes: dict[str, PERHole] = {}

        self.property_context = SVAContext()

    def _generate_decls_for_per(self, per: PER):
        declbase = per.logic.get_hier_path_nonindex()
        declfull = per.logic.get_hier_path("_")
        if per.logic.is_arr_elem():
            declsize = f"[0:{per.logic.parent.size-1}]"
        else:
            declsize = ""
        if isinstance(per, Eq):
            wirename = eq_sva(declfull)
            declname = eq_sva(declbase)
        else:
            # isinstance(per, CondEq):
            wirename = condeq_sva(declfull)
            declname = condeq_sva(declbase)
        return (wirename, declname, declsize)

    def _gen_1t_single(self, mod: Module, invs: list[Inv], ctx: Context, a: str = "a"):
        inv_exprs = []
        for inv in invs:
            inv_exprs.append(inv.get_sva(a))
        inv_spec = "(\n\t" + " && \n\t".join(inv_exprs + ["1'b1"]) + ")"
        return f"wire {inv_sva(mod, ctx)} = {inv_spec};"

    def _gen_1t_comp(
        self, mod: Module, invs: list[Inv], ctx: Context, a: str = "a", b: str = "b"
    ):
        inv_exprs = []
        for inv in invs:
            inv_exprs.append(inv.get_sva(a))
            inv_exprs.append(inv.get_sva(b))
        inv_spec = "(\n\t" + " && \n\t".join(inv_exprs + ["1'b1"]) + ")"
        return f"wire {inv_sva(mod, ctx)} = {inv_spec};"

    def _gen_2t_comp(
        self, mod: Module, pers: list[PER], ctx: Context, a: str = "a", b: str = "b"
    ):
        assigns_ = {}
        decls_ = {}
        declwires_ = []
        for per in pers:
            (wirename, declname, declsize) = self._generate_decls_for_per(per)
            exprname = per.get_sva(a, b)
            assigns_[wirename] = f"assign {wirename} = ({exprname});"
            decls_[declname] = f"logic {declname} {declsize};"
            declwires_.append(wirename)
        svaspec = "(\n\t" + " && \n\t".join(declwires_ + ["1'b1"]) + ")"
        topdecl = f"wire {per_sva(mod, ctx)} = {svaspec};"
        return (assigns_, decls_, topdecl)

    def _generate_decls(self, mod: Module, a: str = "a", b: str = "b"):

        # Holes are not currently supported in submodules
        if mod != self.topmod and len(mod._perholes) != 0:
            logger.error(
                f"Holes not supported yet in sub-modules: found one in {mod.path}"
            )
            sys.exit(1)

        # Wire declarations for invariants
        decls = {}
        # Assignments to invariant wires
        assigns = {}
        # Generate recursively for submodules
        for _, submod in mod._submodules.items():
            (inner_decls, inner_assigns) = self._generate_decls(submod, a, b)
            decls.update(inner_decls)
            assigns.update(inner_assigns)

        # Generate wires for current modules
        (assigns_, decls_, input_decl) = self._gen_2t_comp(
            mod, mod._pycinternal__input, Context.INPUT, a, b
        )
        assigns.update(assigns_)
        decls.update(decls_)

        (assigns_, decls_, state_decl) = self._gen_2t_comp(
            mod, mod._pycinternal__state, Context.STATE, a, b
        )
        assigns.update(assigns_)
        decls.update(decls_)

        (assigns_, decls_, output_decl) = self._gen_2t_comp(
            mod, mod._pycinternal__output, Context.OUTPUT, a, b
        )
        assigns.update(assigns_)
        decls.update(decls_)

        for hole in mod._perholes:
            if hole.active:
                (wirename, declname, declsize) = self._generate_decls_for_per(hole.per)
                exprname = hole.per.get_sva(a, b)
                assigns[wirename] = f"assign {wirename} = ({exprname});"
                decls[declname] = f"logic {declname} {declsize};"

        input_inv_decl_comp = self._gen_1t_comp(
            mod, mod._pycinternal__input_invs, Context.INPUT, a, b
        )
        state_inv_decl_comp = self._gen_1t_comp(
            mod, mod._pycinternal__state_invs, Context.STATE, a, b
        )
        output_inv_decl_comp = self._gen_1t_comp(
            mod, mod._pycinternal__output_invs, Context.OUTPUT, a, b
        )

        input_inv_decl_single = self._gen_1t_single(
            mod, mod._pycinternal__input_invs, Context.INPUT, a
        )
        state_inv_decl_single = self._gen_1t_single(
            mod, mod._pycinternal__state_invs, Context.STATE, a
        )
        output_inv_decl_single = self._gen_1t_single(
            mod, mod._pycinternal__output_invs, Context.OUTPUT, a
        )

        self.specs[mod.path] = ModuleSpec(
            path=mod.path,
            input_spec_decl=input_decl,
            state_spec_decl=state_decl,
            output_spec_decl=output_decl,
            input_inv_spec_decl_comp=input_inv_decl_comp,
            state_inv_spec_decl_comp=state_inv_decl_comp,
            output_inv_spec_decl_comp=output_inv_decl_comp,
            input_inv_spec_decl_single=input_inv_decl_single,
            state_inv_spec_decl_single=state_inv_decl_single,
            output_inv_spec_decl_single=output_inv_decl_single,
        )

        return (decls, assigns)

    def generate_decls(self, a: str = "a", b: str = "b"):

        properties = []

        input_props_1t = f"{inv_sva(self.topmod, Context.INPUT)}"
        state_props_1t = f"{inv_sva(self.topmod, Context.STATE)}"
        output_props_1t = f"{inv_sva(self.topmod, Context.OUTPUT)}"

        input_props_2t = f"{per_sva(self.topmod, Context.INPUT)} && {input_props_1t}"
        state_props_2t = f"{per_sva(self.topmod, Context.STATE)} && {state_props_1t}"
        output_props_2t = f"{per_sva(self.topmod, Context.OUTPUT)} && {output_props_1t}"

        properties.append(
            f"{get_as_assm(TOP_INPUT_1T_PROP)} : assume property\n"
            + f"\t({input_props_1t});"
        )
        self.property_context.assms_1trace.append(TOP_INPUT_1T_PROP)
        properties.append(
            f"{get_as_assm(TOP_STATE_1T_PROP)} : assume property\n"
            + f"\t(!({STEP_SIGNAL}) |-> ({state_props_1t}));"
        )
        self.property_context.assms_1trace.append(TOP_STATE_1T_PROP)
        properties.append(
            f"{get_as_prop(TOP_OUTPUT_1T_PROP)} : assert property\n"
            + f"\t({STEP_SIGNAL} |-> ({state_props_1t} && {output_props_1t}));"
        )
        self.property_context.asrts_1trace.append(TOP_INPUT_1T_PROP)

        properties.append(
            f"{get_as_assm(TOP_INPUT_2T_PROP)} : assume property\n"
            + f"\t({input_props_2t});"
        )
        self.property_context.assms_2trace.append(TOP_INPUT_2T_PROP)
        properties.append(
            f"{get_as_assm(TOP_STATE_2T_PROP)} : assume property\n"
            + f"\t(!({STEP_SIGNAL}) |-> ({state_props_2t}));"
        )
        self.property_context.assms_2trace.append(TOP_STATE_2T_PROP)
        properties.append(
            f"{get_as_prop(TOP_OUTPUT_2T_PROP)} : assert property\n"
            + f"\t({STEP_SIGNAL} |-> ({state_props_2t} && {output_props_2t}));"
        )
        self.property_context.asrts_2trace.append(TOP_OUTPUT_2T_PROP)

        for hole in self.topmod._perholes:
            if hole.active:
                if isinstance(hole.per, Eq):
                    assm_prop = (
                        f"A_{eq_sva(hole.per.logic.get_hier_path_flatindex())} : assume property\n"
                        + f"\t(!({STEP_SIGNAL}) |-> {eq_sva(hole.per.logic.get_hier_path('_'))});"
                    )
                    asrt_prop = (
                        f"P_{eq_sva(hole.per.logic.get_hier_path_flatindex())} : assert property\n"
                        + f"\t(({STEP_SIGNAL}) |-> {eq_sva(hole.per.logic.get_hier_path('_'))});"
                    )
                    self.holes[
                        eq_sva(hole.per.logic.get_hier_path_flatindex())
                    ] = hole.per.logic
                    properties.extend([assm_prop, asrt_prop])
                    self.property_context.holes.append(
                        f"{eq_sva(hole.per.logic.get_hier_path_flatindex())}"
                    )

        return properties, self._generate_decls(self.topmod, a, b)

    def generate_step_decls(self, k: int, a: str = "a") -> list[str]:
        """
        Generate properties for each step in the simulation

        Args:
            k (int): Number of steps
            a (str, optional): Name of the first trace. Defaults to "a".

        Returns:
            list[str]: List of properties for each step
        """
        properties = []
        for i in range(min(k, len(self.topmod._pycinternal__simsteps))):
            assumes = [
                expr.get_sva(a)
                for expr in self.topmod._pycinternal__simsteps[i]._pycinternal__assume
            ]
            assume_spec = "(\n\t" + " && \n\t".join(assumes + ["1'b1"]) + ")"
            asserts = [
                expr.get_sva(a)
                for expr in self.topmod._pycinternal__simsteps[i]._pycinternal__assert
            ]
            assert_spec = "(\n\t" + " && \n\t".join(asserts + ["1'b1"]) + ")"

            properties.append(
                f"{get_as_assm(TOP_STEP_PROP(i))} : assume property\n"
                + f"\t({step_signal(i)} |-> {assume_spec});"
            )
            self.property_context.assms_bmc.append(TOP_STEP_PROP(i))
            properties.append(
                f"{get_as_prop(TOP_STEP_PROP(i))} : assert property\n"
                + f"\t({step_signal(i)} |-> {assert_spec});"
            )
            self.property_context.asrts_bmc.append(TOP_STEP_PROP(i))

        return properties

    def counter_step(self, k: int):
        # Create a counter with k steps
        counter_width = len(bin(k)) - 2
        vtype = f"logic [{counter_width-1}:0]" if counter_width > 1 else "logic"
        vlog = f"""
\t{vtype} {COUNTER};
\talways @(posedge clk) begin
\t    if (fvreset) begin
\t        {COUNTER} <= 0;
\t    end else begin
\t        if ({COUNTER} < {counter_width}'d{k}) begin
\t            {COUNTER} <= ({COUNTER} + {counter_width}'b1);
\t        end
\t    end
\tend
\tlogic {STEP_SIGNAL} = ({COUNTER} == {counter_width}'d{k});
"""
        for i in range(k):
            vlog += f"\tlogic {step_signal(i)} = ({COUNTER} == {counter_width}'d{i});\n"
        return vlog

    def create_pyc_specfile(
        self, k: int, a="a", b="b", filename="temp.pyc.sv", onetrace=False
    ):

        vlog = self.counter_step(k)

        self.topmod.instantiate()
        properties, all_decls = self.generate_decls(a, b)
        properties.extend(self.generate_step_decls(k, a))

        aux_modules = []
        # Get auxiliary modules if any
        for _, aux_mod in self.topmod._auxmodules.items():
            aux_modules.append(aux_mod.get_instance_str(a))

        with open(filename, "w") as f:
            f.write(vlog + "\n")

            for assign in all_decls[0].values():
                f.write(assign + "\n")
            for decl in all_decls[1].values():
                f.write(decl + "\n")

            # Write auxiliary modules
            f.write("\n")
            f.write("/////////////////////////////////////\n")
            f.write("// Auxiliary modules\n")
            for aux_mod in aux_modules:
                f.write(aux_mod + "\n")

            for mod, spec in self.specs.items():
                f.write("\n")
                f.write(f"/////////////////////////////////////\n")
                f.write(f"// Module {mod.get_hier_path()}\n")
                f.write("\n")
                f.write(spec.input_spec_decl + "\n")
                f.write(spec.state_spec_decl + "\n")
                f.write(spec.output_spec_decl + "\n")
                if not onetrace:
                    f.write(spec.input_inv_spec_decl_comp + "\n")
                    f.write(spec.state_inv_spec_decl_comp + "\n")
                    f.write(spec.output_inv_spec_decl_comp + "\n")
                else:
                    f.write(spec.input_inv_spec_decl_single + "\n")
                    f.write(spec.state_inv_spec_decl_single + "\n")
                    f.write(spec.output_inv_spec_decl_single + "\n")

            f.write("\n")
            f.write("/////////////////////////////////////\n")
            f.write("// Assumptions and Assertions for top module\n")
            f.write("\n\n".join(properties))
            f.write("\n")

        logger.info(f"Generated spec file: {filename}")

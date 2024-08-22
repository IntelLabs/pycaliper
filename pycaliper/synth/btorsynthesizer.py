import sys
import logging

from ..per import Module, Eq, CondEq

from ..btorinterface.pycbtorsymex import PYCBTORSymex

logger = logging.getLogger(__name__)


class BTORSynthesizer:
    def __init__(self, slv: PYCBTORSymex):
        self.topmod: Module = None
        self.slv = slv

    def synthesize(self, module: Module) -> bool:
        """
        Perform hole-synthesis for a single module w.r.t. the following property:
            input_eq && state_eq |-> ##1 output_eq && state_eq
        """
        # Instantiate the module
        self.topmod = module
        self.topmod.instantiate()

        if not self.topmod._perholes:
            logger.error(
                "No holes to fill in a synthesizer, please use a verifier. Exiting."
            )
            sys.exit(1)

        if self.topmod._caholes:
            logger.error(
                "Ctrl holes not supported in this (BTOR) synthesizer. Exiting."
            )
            sys.exit(1)

        eq_assms = []
        eq_assrts = []
        condeq_assms = []
        condeq_assrts = []

        # Generate the assumptions and assertions
        for p in self.topmod._input:
            match p:
                case Eq():
                    eq_assms.append(p.logic)
                case CondEq():
                    condeq_assms.append((p.cond, p.logic))
        for p in self.topmod._state:
            match p:
                case Eq():
                    eq_assms.append(p.logic)
                    eq_assrts.append(p.logic)
                case CondEq():
                    condeq_assms.append((p.cond, p.logic))
                    condeq_assrts.append((p.cond, p.logic))
        for p in self.topmod._output:
            match p:
                case Eq():
                    eq_assrts.append(p.logic)
                case CondEq():
                    condeq_assrts.append((p.cond, p.logic))

        self.slv.add_eq_assms(eq_assms)
        self.slv.add_condeq_assms(condeq_assms)
        self.slv.add_eq_assrts(eq_assrts)
        self.slv.add_condeq_assrts(condeq_assrts)

        self.slv.add_hole_constraints([hol.per.logic for hol in self.topmod._perholes])

        # Perform verification
        return self.slv.inductive_two_safety_syn()

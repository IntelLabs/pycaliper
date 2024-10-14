import logging
import sys

from ..btorinterface.pycbtorsymex import PYCBTORSymex
from ..per import Module, Eq, CondEq

from .invverifier import InvVerifier

logger = logging.getLogger(__name__)


class BTORVerifier2Trace(InvVerifier):
    def __init__(self, slv: PYCBTORSymex):
        self.topmod = None
        self.slv = slv

    def verify(self, module: Module) -> bool:
        """
        Perform verification for a single module of the following property:
            input_eq && state_eq |-> ##1 output_eq && state_eq
        """
        # Instantiate the module
        self.topmod = module
        self.topmod.instantiate()

        if self.topmod._perholes or self.topmod._caholes:
            logger.error(
                "Holes not supported in a verifier, please use a synthesizer. Exiting."
            )
            sys.exit(1)

        eq_assms = []
        eq_assrts = []
        condeq_assms = []
        condeq_assrts = []

        # Generate the assumptions and assertions
        for p in self.topmod._pycinternal__input:
            match p:
                case Eq():
                    eq_assms.append(p.logic)
                case CondEq():
                    condeq_assms.append((p.cond, p.logic))
        for p in self.topmod._pycinternal__state:
            match p:
                case Eq():
                    eq_assms.append(p.logic)
                    eq_assrts.append(p.logic)
                case CondEq():
                    condeq_assms.append((p.cond, p.logic))
                    condeq_assrts.append((p.cond, p.logic))
        for p in self.topmod._pycinternal__output:
            match p:
                case Eq():
                    eq_assrts.append(p.logic)
                case CondEq():
                    condeq_assrts.append((p.cond, p.logic))

        self.slv.add_eq_assms(eq_assms)
        self.slv.add_condeq_assms(condeq_assms)
        self.slv.add_eq_assrts(eq_assrts)
        self.slv.add_condeq_assrts(condeq_assrts)

        logger.debug(f"eq_assms: %s, eq_assrts: %s", eq_assms, eq_assrts)

        # Perform verification
        return self.slv.inductive_two_safety()
